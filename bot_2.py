# -*- coding: utf-8 -*-
"""
Created on Sat Aug 15 21:45:14 2020

@author: Thomas DeWitt

Contributor: Andrew Lu
"""

# ArmOfState2

import discord
import csv
import pickle
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
# from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
print(tf.__version__)
print(keras.__version__)

# TO-DO:
# DONE - Create and import ExeNet tokenizer and ExeNet model alongside ToxiNet resources
# Dynamically handle rankings
# Create user list
# Handle new users coming in

def read_token():
    with open("token.txt", "r") as file:
        lines = file.readlines()
        return lines[0].strip()

# Format: <string uid> <float 2 score>\n
def load_scores():
    scores = {}
    try:
        with open("scores.csv", "r", newline="") as csvfile:
            lines = csv.reader(csvfile)
            for line in lines:
                scores[str(line[0])] = float(line[1])
        return scores
    except:
        with open("scores.csv", "w"):
            return scores
    
def save_scores():  # have it update every 10 minutes or something eventually
    with open("scores.csv", "w", newline="") as csvfile:
        save = csv.writer(csvfile)
        for pairs in toxiscores.items():
            save.writerow([str(pairs[0]), str(pairs[1])])

def load_preprocessing():
    with open('toxic_tokenizer.pickle', 'rb') as handle:
        toxic_tokenizer = pickle.load(handle)  # load ToxiNet tokenizer
    with open('exe_tokenizer.pickle','rb') as handle:
        exe_tokenizer = pickle.load(handle)  # load ExeNet tokenizer
    max_length = 400  # cut/pad all sentences to 400 tokens (words)
    trunc_type = 'post'
    padding_type = 'post'
    embedding_dimension = 100
    return toxic_tokenizer, exe_tokenizer, max_length, trunc_type, padding_type, embedding_dimension

def score_text(model, toxic_preds, message_string, tokenizer, max_length, padding_type, trunc_type):
    if toxic_preds <= 0.75:
        score = 0
    else:
        exe_tokens = tokenizer.texts_to_sequences(message_string)
        exe_ready = pad_sequences(exe_tokens, maxlen=max_length, padding=padding_type, truncating=trunc_type)
        exe_preds = model.predict(exe_ready)
        score = np.argmax(exe_preds, axis=1)
    return score

def manage_toxiscores(uid, message_score):
    if uid not in toxiscores.keys():
        toxiscores[uid] = 0.00
    
    user_score = toxiscores[uid]
    
    if message_score <= 0.00:  # Losing toxicity
        user_score -= modifier(user_score) * loss
        user_score = 0.00 if toxiscores[uid] <= 0.00 else user_score
    else:  # Gaining toxicity
        user_score += modifier(user_score) * message_score * gain

    toxiscores[uid] = round(user_score, 2)

"""
Notes:
For handling users, instead of using User.name maybe use User.id

"""
# Tokens & Prefix
token = read_token()
prefix = "?"

# Master users (Convert to uid?)
master_users = ["das.lionfish#9316"]

# Scraping info (Eventually write to file instead)
messages = []
authors = []

# Model statuses
scrape_messages = False
prep_to_analyze = False
model_ready = False

# Load toxicity scores
toxiscores = load_scores()

# Toxicity score modifier & factor modifier should be multiplied by for gaining/losing toxicity, 1 gain/loss default
modifier = lambda x : round(pow(1.075, -3/8 * x), 2)
gain = 1
loss = 1

client = discord.Client()

@client.event
async def on_message(message):
    # don't reply to self
    if message.author == client.user:
        return
    
    if message.content.startswin('!#scrape'):
        if str(message.author) in master_users:
            scrape_messages = True
            await message.channel.send('WARNING: all messages following this message will be filed for training purpose.')
    
    if message.content.startswith('!#init_network'):
        if str(message.author) in master_users:
            await message.channel.send('Unpacking model...')
            toxic_model = tf.keras.models.load_model('saved_model/ToxiNet')
            exe_model = tf.keras.models.load_model('saved_model/ExeNet')
            toxic_tokenizer, exe_tokenizer, max_length, trunc_type, padding_type, embedding_dimension = load_preprocessing()
            # edit above to spec as ToxiNet params, load ExeNet model and params
            # above line also now loads ExeNet tokenizer as exe_tokenizer
            model_ready = True
            await message.channel.send('Models loaded.  Displaying ToxiNet parameters...')
            stringlist = []
            toxic_model.summary(print_fn=lambda x: stringlist.append(x))
            short_model_summary = "\n".join(stringlist)
            await message.channel.send(short_model_summary)
            
    
    if message.content.startswith('!#process'):
            if str(message.author) in master_users:
                if model_ready == True:
                    prep_to_analyze = True
                    await message.channel.send('Analysis framework active.')
                else:
                    await message.channel.send('Models not loaded.  Please load models.')
    
    if scrape_messages == True:  # Eventually directly write to a file, also maybe only from one channel?
        messages.append(str(message.content))
        authors.append(str(message.author))
        
    if prep_to_analyze == True:
        words = str(message.content)
        toxic_tokens = toxic_tokenizer.texts_to_sequences(words)
        toxic_ready = pad_sequences(toxic_tokens, maxlen=max_length, padding=padding_type, truncating=trunc_type)
        toxic_preds = toxic_model.predict(toxic_ready)
        toxic_results = np.argmax(toxic_preds, axis=1)
        toxic_score = score_text(exe_model, toxic_results, words, exe_tokenizer, max_length, padding_type, trunc_type)
        # add in ExeNet functions here

    if message.content == '?hello':
        reply = 'Greetings, citizen.'
        await message.channel.send(reply)
    
    if message.content.startswith('!#killall'):
        if str(message.author) in master_users:
            await message.channel.send('Saving data...')
            data = pd.DataFrame(data={'user': authors, 'message': messages})
            data.to_csv('C:/Users/Thomas DeWitt/Downloads/discord_messages.csv', sep=',', index=False)
            await client.logout()
    



client.run(token)

print('Connected to client.')
