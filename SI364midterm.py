###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
import os
import requests
import json
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
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

#get_or_create_queen

# get_or_create_challenge

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
    prize = db.Column(db.String)
    queen_id = db.Column(db.Integer, db.ForeignKey('queens.id'))


###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your name.",validators=[Required()])
    submit = SubmitField()



#######################
###### VIEW FXNS ######
#######################

@app.route('/')
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name = form.name.data
        newname = Name(name)
        db.session.add(newname)
        db.session.commit()
        return redirect(url_for('all_names'))
    return render_template('base.html',form=form)

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)






## Code to run the application...
if __name__ == '__main__':
    db.create_all()
    app.run(use_reloader=True,debug=True)
