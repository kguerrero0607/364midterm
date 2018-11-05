###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
import os
import requests
import json
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy

## App setup code
app = Flask(__name__)
app.debug = True

## All app.config values
app.config['SECRET_KEY'] = 'supersecretstring'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:ROCKCITY123@localhost/364Midterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################

# check if there exists a queen by this name in the database.
# if so, return her info. if not, create and save queen to db and return instance
def get_or_create_queen(name):
    queen = Queen.query.filter_by(name=name).first()

    if not queen:
        # get queen's id from API
        response = requests.get('http://www.nokeynoshade.party/api/queens', params={
                   'name': name
        })
        json_obj = json.loads(response.text)
        queen_id = json_obj[0]['id']

        queen = Queen(id=queen_id, name=name)
        db.session.add(queen)
        db.session.commit()

    return queen

def get_or_create_challenge(queen_id):
    challenge = Challenge.query.filter_by(queen_id=queen_id).first()

    if not challenge:
        # use queen's id to get all their info from API
        url = 'http://www.nokeynoshade.party/api/queens/{}'.format(queen_id)
        response = requests.get(url)
        json_obj = json.loads(response.text)

        # get list of ids of all challenges given queen won
        victory_id_list = []
        challenge_list = json_obj['challenges']
        for x in challenge_list:
            if x['type'] == 'main':
                if x['won'] == True:
                    victory_id_list.append(x['id'])

        # search API for challenge ID to get description, prize, and episode ID
        for x in victory_id_list:
            challenge_url = 'http://www.nokeynoshade.party/api/challenges/{}'.format(x)
            challenge_response = requests.get(challenge_url)
            challenge_json_obj = json.loads(challenge_response.text)

            description = challenge_json_obj['description']
            prize = challenge_json_obj['prize']
            episode_id = challenge_json_obj['episodeId']

            # search API using ep ID to get episode ep title
            episode_url = 'http://www.nokeynoshade.party/api/episodes/{}'.format(episode_id)
            episode_response = requests.get(episode_url)
            episode_json_obj = json.loads(episode_response.text)
            ep_title = episode_json_obj['title']

            challenge = Challenge(id=x, ep_title=ep_title, description=description, prize=prize, queen_id=queen_id)
            db.session.add(challenge)
            db.session.commit()

    return challenge


##################
##### MODELS #####
##################

class Queen(db.Model):
    __tablename__ = 'queens'
    id = db.Column(db.Integer, primary_key=True, autoincrement=False) # autoincrement not needed - API provides unique ID for each queen
    name = db.Column(db.String)
    challenges = db.relationship('Challenge', backref='queen')

class Challenge(db.Model):
    __tablename__ = 'challenges'
    id = db.Column(db.Integer, primary_key=True, autoincrement=False) # autoincrement not needed - API provides unique ID for each challenge
    ep_title = db.Column(db.String)
    description = db.Column(db.String)
    prize = db.Column(db.String, default = 'None')
    queen_id = db.Column(db.Integer, db.ForeignKey('queens.id'))
    def __repr__(self):
        return 'ID: {}, Episode: {}, Desc: {}, Prize: {}, QueenId: {}'.format(id,ep_title,description,prize,queen_id)


###################
###### FORMS ######
###################

class QueenForm(FlaskForm):
    name = StringField("Enter the name of a RuPaul's Drag Race queen (please use proper capitalization): ", validators=[Required()])
    submit = SubmitField()

    # custom validator to ensure queen entered was actually a RPDR queen
    def validate_name(self, field):
        full_queen_list = []
        baseurl = 'http://www.nokeynoshade.party/api/queens/all'
        response = requests.get(baseurl)
        json_obj = json.loads(response.text)
        for x in json_obj:
            full_queen_list.append(x['name'])

        if field.data not in full_queen_list:
            raise ValidationError('ERROR: Name entered is not a valid RPDR queen!')



#######################
###### VIEW FXNS ######
#######################

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/', methods=['GET','POST'])
def index():
    form = QueenForm()
    name = ''

    if form.validate_on_submit():
        name = form.name.data

        specific_queen = Queen.query.filter_by(name=name).first()
        if specific_queen:
            flash('*** You already searched for that queen! Find her below! ***')
            return redirect(url_for('all_queens'))

        if not specific_queen:
            queen = get_or_create_queen(name)
            challenge = get_or_create_challenge(queen.id)
            flash('You successfully searched for a new queen!')

    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))

    return render_template('index.html',form=form)

@app.route('/all_queens')
def all_queens():
    queen_names = []
    all_queens = Queen.query.all()
    for x in all_queens:
        queen_names.append(x.name)
    queen_names = sorted(queen_names)

    return render_template('all_queens.html', queens=queen_names)

@app.route('/all_challenges')
def all_challenges():
    challenges = Challenge.query.all()
    all_challenges = [(c.ep_title, c.description, c.prize, Queen.query.filter_by(id=c.queen_id).first().name) for c in challenges]

    return render_template('all_challenges.html', all_challenges=all_challenges)

@app.route('/<name>')
def queen_info(name):
    name = name.replace('%20', ' ')
    specific_queen = Queen.query.filter_by(name=name).first()

    if not specific_queen:
        flash("That queen wasn't found. Try searching her name!")
        return redirect(url_for('index'))

    challenges = Challenge.query.filter_by(queen_id=specific_queen.id).all()
    challenges_won = [(c.ep_title, c.description) for c in challenges]



    return render_template('queen_info.html',queen=specific_queen,chal=challenges_won)

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)



## Code to run the application...
if __name__ == '__main__':
    db.create_all()
    app.run(use_reloader=True,debug=True)
