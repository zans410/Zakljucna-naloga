from flask import flask, requests, render_template, redirect, url_for, jsonify
import bcrypt

#Da se ne vidi gesla ko ga vpisuješ
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
