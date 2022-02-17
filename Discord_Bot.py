# -*- coding: utf-8 -*-
"""
Created on Thu Nov 11 13:13:15 2021
@author: derph
"""

import nest_asyncio
nest_asyncio.apply()

import discord
from discord.ext import commands

import asyncio
import string
import random
import csv
import time
from pymongo import MongoClient
import requests

# import keep_alive
intents = discord.Intents.default()
intents.reactions = True

tokenIn = open("Token Key.txt", "r+")
token = tokenIn.readline().rstrip()

client = commands.Bot(command_prefix='+')
client.remove_command('help')
mongo = MongoClient(tokenIn.readline().rstrip())
client.quiz = mongo.quizInfo.quizinfos
client.quizInfo = {}
botname = tokenIn.readline().rstrip()

ANSWERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
emojis = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯']
answer_dict = {'🇦': "A", '🇧': "B", '🇨': "C", '🇩': "D", '🇪': "E", '🇫': "F", '🇬': "G", '🇭': "F", '🇮': "I",
               '🇯': "J"}
medals = ["🥇", "🥈", "🥉"]
posEmojis = ["🇦", "🇧"]
checkMarks = ["✔️", "❌"]
arrows = ["⬅️", "➡️"]
tokenIn.close()


@client.event
async def on_ready():
    print("Bot is Ready")
    await client.change_presence(activity=discord.Game("+help for more info"))


@client.command()
async def run(message, Id):
    channel = message.channel
    msg_limit = 5
    MessageMan = True
    if client.quizInfo.get(channel.id):
        await channel.send(
            embed=discord.Embed(
                title="Quiz already running in this channel! Please allow it to finish or use a different channel.",
                color=discord.Colour.red()))
        return
    client.quizInfo[channel.id] = {"players": {}, "elimination": False, "shuffle": False}
    try:
        doc = client.quiz.find_one({"_id": Id})
        if doc["privacy"] == "private":
            if doc["name"] != str(message.author.id):
                client.quizInfo.pop(channel.id)
                await channel.send(
                    embed=discord.Embed(title="You are not authorized to run this quiz", colour=discord.Colour.red()))
                return
        questions = doc["questions"]

        await channel.send(
            embed=discord.Embed(title="You have 10 seconds to react to the reaction below and join the game.",
                                color=discord.Colour.blue()))

        while True:            
            InvMsg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
            if InvMsg is not None:
                if msg_limit >= 20:
                    msg_limit //= 3
                break
            msg_limit += 5

        await InvMsg.add_reaction(checkMarks[0])

        def FalseReaction(rxn, user):
            message = rxn.message
            channel = message.channel
            if rxn.emoji == checkMarks[0] and str(user.id) != botname and str(
                    message.author.id) == botname and InvMsg == message:
                client.quizInfo[channel.id]["players"][user.name] = 0
            return False

        try:
            await client.wait_for("reaction_add", check=FalseReaction, timeout=10)
        except:
            pass

        while 1:
            InvMsg = await channel.history(limit=msg_limit).find(lambda m: m.id == InvMsg.id)
            if InvMsg is not None:
                if msg_limit >= 20:
                    msg_limit //= 3
                break
            msg_limit += 5

        if InvMsg.reactions[0].count <= 1:
            client.quizInfo.pop(channel.id)
            await channel.send(
                embed=discord.Embed(title="No players joined. Ending the game.", color=discord.Colour.red()))
            return
        await channel.send(embed=discord.Embed(
            title="Press 🇦 to play by elimination (wrong answers get you kicked) or 🇧 to play by subtraction (wrong "
                  "answers lead to a score deduction).",
            color=discord.Colour.blue()))

        while 1:
            OptMsg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
            if OptMsg is not None:
                if msg_limit >= 20:
                    msg_limit //= 3
                break
            msg_limit += 5

        await OptMsg.add_reaction(posEmojis[0])
        await OptMsg.add_reaction(posEmojis[1])

        # Ensures that only player in game can vote
        def setCheck(rxn, user):
            if rxn.emoji in posEmojis and client.quizInfo[channel.id]["players"].get(user.name) is not None:
                client.quizInfo[channel.id]["elimination"] = True if rxn.emoji == posEmojis[0] else False
                return True
            else:
                return False

        try:
            await client.wait_for("reaction_add", check=setCheck, timeout=20)
        except:
            try:
                await OptMsg.clear_reaction(posEmojis[0])
                await OptMsg.clear_reaction(posEmojis[1])
            except:
                pass
            await OptMsg.edit(
                embed=discord.Embed(title="No response given. Ending the quiz.", colour=discord.Colour.red()))
            client.quizInfo.pop(channel.id)
            return
        try:
            await OptMsg.clear_reaction(posEmojis[0])
            await OptMsg.clear_reaction(posEmojis[1])
        except:
            MessageMan = False
        if client.quizInfo[channel.id]["elimination"]:
            await OptMsg.edit(embed=discord.Embed(title="You are playing by elimination", color=discord.Colour.blue()))
        else:
            await OptMsg.edit(
                embed=discord.Embed(title="You are playing with score deductions", color=discord.Colour.blue()))

        await channel.send(embed=discord.Embed(
            title="Would you like questions to be randomized?",
            color=discord.Colour.blue()))

        while 1:
            RandQ = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
            if RandQ is not None:
                break
            msg_limit += 5

        await RandQ.add_reaction(checkMarks[0])
        await RandQ.add_reaction(checkMarks[1])

        # Function for checking for reaction given
        def randCheck(rxn, user):
            if rxn.emoji in checkMarks and client.quizInfo[channel.id]["players"].get(user.name) is not None:
                client.quizInfo[channel.id]["shuffle"] = True if rxn.emoji == checkMarks[0] else False
                return True
            else:
                return False

        try:
            await client.wait_for("reaction_add", check=randCheck, timeout=20)
        except:
            if MessageMan:
                await RandQ.clear_reaction(checkMarks[0])
                await RandQ.clear_reaction(checkMarks[1])
            await RandQ.edit(
                embed=discord.Embed(title="No response given. Ending the quiz.", colour=discord.Colour.red()))
            client.quizInfo.pop(channel.id)
            return
        if MessageMan:
            await RandQ.clear_reaction(checkMarks[0])
            await RandQ.clear_reaction(checkMarks[1]) 
        if client.quizInfo[channel.id]["shuffle"]:
            random.shuffle(questions)
            await RandQ.edit(embed=discord.Embed(title="Questions have been shuffled", color=discord.Colour.blue()))
        else:
            await RandQ.edit(
                embed=discord.Embed(title="Question order maintained", color=discord.Colour.blue()))

        await channel.send(
            embed=discord.Embed(title="Starting! Remember to wait for answers to show up before responding.",
                                color=discord.Colour.green()))
        Qnum = 1
        winner = ""
        for iteration, row in enumerate(questions):
            if len(client.quizInfo[channel.id]["players"]) == 1 and client.quizInfo[channel.id]["elimination"]:

                for i in client.quizInfo[channel.id]["players"].keys():
                    winner = i

                await channel.send(
                    embed=discord.Embed(
                        title=winner + " wins for being the last survivor!",
                        color=discord.Colour.blue()))
                podium = discord.Embed(
                    title="Final Podium",

                    color=discord.Colour.gold()
                )
                podium.add_field(name=arrows[1], value=winner, inline=False)
                await channel.send(embed=podium)
                client.quizInfo.pop(channel.id)
                break
            #row = row.split("ȟ̵̢̨̤͕̔͊̓͒ͅ")
            for i in range(0, len(row)):
                if row[i] == '':
                    if i == 2:
                        row[i] = "None"
                    else:
                        row[i] = False
            for i in range(0, row.count(False)):
                row.remove(False)
            row[0] = str(Qnum)
            Qnum += 1

            embed = discord.Embed(
                title="Question " + row[0],
                description=row[1],

                colour=discord.Colour.blue()
            )
            if row[2] != "None":
                embed.set_image(url=row[2])
                # await channel.send(row[2])
            await channel.send(embed=embed)

            while 1:
                msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
                if msg is not None:
                    if msg_limit >= 20:
                        msg_limit //= 3
                    break
                msg_limit += 5

            for emoji in emojis[:len(row[5:])]:
                await msg.add_reaction(emoji)

            embedstart = time.time()
            for i, e in enumerate(emojis[:len(row[5:])]):
                if row[5 + i] == "TRUE":
                    row[5 + i] = "True"
                elif row[5 + i] == "FALSE":
                    row[5 + i] = "False"
                embed.add_field(name=e, value=row[5 + i])
            embed.set_footer(text="You have " + row[4] + " seconds")
            await msg.edit(embed=embed)
            def check(rxn, user):
                message = rxn.message
                if len(message.embeds) == 0:
                    return False
                if user.id != botname and client.quizInfo[channel.id]["players"].get(
                        user.name) is not None and message.id == msg.id:
                    return True
                else:
                    return False
            embedend= time.time()
            embedtime = embedend - embedstart

            await asyncio.sleep(1.5 - embedtime)



            answer = "Fail"
            t0 = time.perf_counter()
            try:
                answer = await client.wait_for("reaction_add", timeout=float(row[4]), check=check)
            except:
                await channel.send("No Response Given")
            if type(answer) != str:
                t1 = time.perf_counter()
                times = t1 - t0

                pts = 300 - 300 * (times / (int(row[4]) / 1.5)) ** 2
                if pts < 10:
                    pts = 10
                if answer_dict.get(answer[0].emoji) and answer_dict[answer[0].emoji] == row[3]:
                    await channel.send(
                        "Correct!  " + answer[1].name + " will be awarded " + str(int(round(pts, 0))) + " points.")
                    client.quizInfo[channel.id]["players"][answer[1].name] += int(round(pts, 0))
                else:
                    await channel.send("WRONG! The correct answer is " + row[3])
                    if client.quizInfo[channel.id]["elimination"]:
                        client.quizInfo[channel.id]["players"].pop(answer[1].name, None)
                        await channel.send(answer[1].name + " will be kicked!")
                    else:
                        client.quizInfo[channel.id]["players"][answer[1].name] -= int(round(pts, 0))
                        await channel.send(answer[1].name + " will lose " + str(int(round(pts, 0))) + " points!")
            client.quizInfo[channel.id]["players"] = dict(
                sorted(client.quizInfo[channel.id]["players"].items(), key=lambda kv: kv[1], reverse=True))
            rankings = discord.Embed(
                title="Rankings",

                color=discord.Colour.red()
            )
            rank = 1
            for player in client.quizInfo[channel.id]["players"].keys():
                rankings.add_field(name=str(rank) + ". " + player,
                                   value=str(client.quizInfo[channel.id]["players"][player]) + " point",
                                   inline=False)
                rank += 1
            await channel.send(embed=rankings)

            embedstart = time.time()

            if iteration == len(questions) - 1:
                Final = discord.Embed(
                    title="Final Podium",

                    color=discord.Colour.gold()
                )
                rank = 1
                for player in client.quizInfo[channel.id]["players"].keys():
                    Final.add_field(name=medals[rank - 1], value=player, inline=False)
                    rank += 1
                    if rank == 4: break
                await channel.send(embed=Final)
                client.quizInfo.pop(channel.id)
                break

            embedend = time.time()
            embedtime = embedend - embedstart
            await asyncio.sleep(1.5 - embedtime)

    except Exception as e:
        print(e)
        if client.quizInfo.get(channel.id):
            client.quizInfo.pop(channel.id)
        await channel.send(embed=discord.Embed(title="Invalid Quiz Code Given or Invalid Quiz Set",
                                               color=discord.Colour.red()))


# creates a 4 letter id and checks if it is unique. If not, reiterates. Returns unique id.
def quizcodemaker(col):
    filename = ''.join(random.choice(string.ascii_uppercase) for i in range(4))
    doc = col.find_one({"_id": "Key"})
    codes = doc["Codes"]
    if filename in codes:
        quizcodemaker(col)
    return filename


@client.command()
async def upload(ctx):
    msg_limit = 5
    author = ctx.author
    channel = ctx.channel
    quiz = ""
    EmbedList = []
    Qnum = 1

    await ctx.send("Please upload your .CSV file.")

    def check(message):
        return message.author == ctx.author and message.attachments[0].filename.endswith('.csv')

    try:
        message = await client.wait_for('message', timeout=25.0, check=check)
        file = message.attachments
        unique_quizcode = quizcodemaker(client.quiz)

        if len(file) > 0 and file[0].filename.endswith('.csv'):
            quiz = requests.get(file[0].url).content.decode("utf-8")
            quiz = quiz.split("\n")
            quiz = list(csv.reader(quiz))

            # checks if you used the template
            templatecheck = "Question No.,Question,Image URL,Answer (letter),Time,A,B,C,D,E,F,G,H,I,J"
            if templatecheck not in ",".join(quiz[5]):
                await channel.send(embed=discord.Embed(
                    title="Invalid .csv format! Please follow the template and follow the instructions listed. You "
                          "can find the quiz template at "
                          "https://docs.google.com/spreadsheets/d/1H1Fg5Lw1hNMRFWkorHuAehRodlmHgKFM8unDjPZMnUg/edit"
                          "#gid=196296521",
                    colour=discord.Colour.red()))
                return

            for row in quiz[6:]:
                if set(list(row)) == {''}:
                    continue
                for i in range(0, len(row)):
                    if row[i] == "":
                        if i == 2:
                            row[i] = "None"
                        else:
                            row[i] = False
                for i in range(0, row.count(False)):
                    row.remove(False)
                row[0] = str(Qnum)
                Qnum += 1
                embed = discord.Embed(
                    title="Question " + row[0],
                    description=row[1],

                    colour=discord.Colour.blue()
                )
                if row[2] != "None":
                    # checks if the image link works
                    types = [".jpg", ".jpeg", ".png", ".gif"]
                    if not any(x in row[2] for x in types):
                        await channel.send(embed=discord.Embed(
                            title="Invalid image URL for question " + row[
                                0] + "! Please double check that you inputted a proper image URL (Right-click, "
                                     "\"copy image address\", paste).",
                            colour=discord.Colour.red()))
                        return
                    embed.set_image(url=row[2])
                # await channel.send(row[2])
                for i, e in enumerate(emojis[:len(row[5:])]):
                    if row[5 + i] == "TRUE":
                        row[5 + i] = "True"
                    elif row[5 + i] == "FALSE":
                        row[5 + i] = "False"

                    # checks if you have a correct answer choice
                    validanswerchoice = False
                    if row[3].islower():
                        await channel.send(
                            "Answer choices are case sensitive! Please change your correct answer choice for question " +
                            row[0])
                        return
                    if row[3] in ANSWERS[:len(row[5:])]:
                        validanswerchoice = True
                    if not validanswerchoice:
                        await channel.send(
                            "Question " + row[0] + " does not have a valid correct answer! (\"" + row[
                                3] + "\") Please check the template for correct formatting.")
                        return
                    if ANSWERS[i] == row[3]:
                        embed.add_field(name=e, value=row[5 + i] + " (answer)")
                    else:
                        embed.add_field(name=e, value=row[5 + i])

                    # checks if time is valid

                    if not row[4].isdigit():
                        await channel.send(
                            "Question " + row[0] + " does not have a valid time! (\"" + row[
                                4] + "\")")
                        return

                embed.set_footer(text="You have " + row[4] + " seconds")
                EmbedList.append(embed)

            j = 0
            await channel.send(embed=EmbedList[j])

            while 1:
                embed = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
                if embed is not None:
                    break
                msg_limit += 5

            await embed.add_reaction(arrows[0])
            await embed.add_reaction(arrows[1])
            await embed.add_reaction(checkMarks[0])
            await channel.send(
                embed=discord.Embed(
                    title="These are the questions you made. Please navigate through them using the arrow keys. Press "
                          "the checkmark reaction once you're done checking",
                    colour=discord.Colour.dark_magenta()))

            while 1:
                msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
                if msg is not None:
                    break
                msg_limit += 5


            doneChecking = False

            def checkdirection(reaction, user):
                return (user == message.author and (str(reaction.emoji) == '✔️' or str(
                    reaction.emoji) == arrows[0] or str(
                    reaction.emoji) == arrows[1])) and reaction.message == embed

            def checkRemoveDirection(payload):
                guild = client.get_guild(payload.guild_id)
                reaction = payload.emoji.name
                return (payload.user_id == ctx.author.id and (str(reaction) == '✔️' or str(
                    reaction) == arrows[0] or str(
                    reaction) == arrows[1])) and payload.message_id == embed.id

            while not doneChecking:
                pending_tasks = [client.wait_for('raw_reaction_remove', check=checkRemoveDirection),
                                 client.wait_for('reaction_add', check=checkdirection)]
                done_tasks, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
                quizCheck = None
                for task in done_tasks:
                    quizCheck = await task
                try:
                    if quizCheck[0].emoji == arrows[0]:
                        j -= 1
                        if j < 0:
                            j = len(EmbedList) - 1
                        await embed.edit(embed=EmbedList[j])
                    if quizCheck[0].emoji == arrows[1]:
                        j += 1
                        if j > len(EmbedList) - 1:
                            j = 0
                        await embed.edit(embed=EmbedList[j])
                    if quizCheck[0].emoji == checkMarks[0]:
                        doneChecking = True
                except:
                    if quizCheck.emoji.name == arrows[0]:
                        j -= 1
                        if j < 0:
                            j = len(EmbedList) - 1
                        await embed.edit(embed=EmbedList[j])
                    if quizCheck.emoji.name == arrows[1]:
                        j += 1
                        if j > len(EmbedList) - 1:
                            j = 0
                        await embed.edit(embed=EmbedList[j])
                    if quizCheck.emoji.name == checkMarks[0]:
                        doneChecking = True
        await embed.delete()
        await msg.edit(
            embed=discord.Embed(title="Is this the quiz set you wish to create?", colour=discord.Colour.purple()))
        await msg.add_reaction(checkMarks[0])
        await msg.add_reaction(checkMarks[1])

        def checkanswer(reaction, user):
            return user.id == message.author.id and (str(reaction.emoji) == '✔️' or str(reaction.emoji) == '❌')

        try:
            userAnswer = await client.wait_for('reaction_add', timeout=20.0, check=checkanswer)
            if userAnswer[0].emoji == checkMarks[0]:
                privacySetting = "public"
                quizname = quiz[2][0]

                try:
                    await msg.clear_reaction(checkMarks[0])
                    await msg.clear_reaction(checkMarks[1])

                    await msg.edit(embed=discord.Embed(
                        title="This quiz set is currently set as public. Would you like it private?",
                        colour=discord.Colour.green()))
                except:
                    await channel.send(embed=discord.Embed(
                        title="This quiz set is currently set as public. Would you like it private?",
                        colour=discord.Colour.green()))

                    while 1:
                        msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
                        if msg is not None:
                            break
                        msg_limit += 5

                await msg.add_reaction(checkMarks[0])
                await msg.add_reaction(checkMarks[1])
                try:

                    privacy = await client.wait_for("reaction_add", timeout=20.0, check=checkanswer)
                    if privacy[0].emoji == checkMarks[0]:
                        privacySetting = "private"
                except asyncio.TimeoutError:
                    try:
                        await msg.clear_reaction(checkMarks[0])
                        await msg.clear_reaction(checkMarks[1])
                        await msg.edit(embed=discord.Embed(
                            title="You timed out!",
                            colour=discord.Colour.red()))
                        return
                    except:
                        await channel.send(mbed=discord.Embed(
                            title="You timed out!",
                            colour=discord.Colour.red()))
                        while 1:
                            msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
                            if msg is not None:
                                break
                            msg_limit += 5
                try:
                    await msg.clear_reaction(checkMarks[0])
                    await msg.clear_reaction(checkMarks[1])

                    await msg.edit(embed=discord.Embed(
                        title="Okay, your quiz set will be " + privacySetting + ". Your current quiz name is **\"" + quizname + "\"**. Would you like to change it?",
                        colour=discord.Colour.red()))
                except:
                    await channel.send(embed=discord.Embed(
                        title="Okay, your quiz set will be " + privacySetting + ". Your current quiz name is **\"" + quizname + "\"**. Would you like to change it?",
                        colour=discord.Colour.red()))
                    while 1:
                        msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
                        if msg is not None:
                            break
                        msg_limit += 5

                await msg.add_reaction(checkMarks[0])
                await msg.add_reaction(checkMarks[1])

                # creates quiz and uploads it into the database
                def createquiz():
                    client.quiz.update_one({"_id": "Key"},
                                           {'$addToSet': {"Codes": unique_quizcode}})

                    client.quiz.insert_one(
                        {"_id": unique_quizcode, "name": str(author.id), "quizName": quizname,
                         "questions": [], "privacy": privacySetting})

                    quiz = requests.get(file[0].url).content.decode("utf-8")
                    quiz = quiz.split("\n")
                    quiz = list(csv.reader(quiz))
                    for row in quiz[6:]:
                        if set(list(row)) == {''}:
                            continue
                        y = row
                        #y = 'ȟ̵̢̨̤͕̔͊̓͒ͅ'.join(row)
                        client.quiz.update_one({"_id": unique_quizcode},
                                               {'$addToSet': {"questions": y}})

                try:
                    changeName = await client.wait_for('reaction_add', timeout=20.0, check=checkanswer)
                    if changeName[0].emoji == checkMarks[0]:
                        nameDesired = False
                        while not nameDesired:
                            try:
                                await msg.clear_reaction(checkMarks[0])
                                await msg.clear_reaction(checkMarks[1])

                                await msg.edit(embed=discord.Embed(
                                    title="Please type what you would like to name your quiz.",
                                    colour=discord.Colour.orange()))
                            except:
                                await msg.edit(embed=discord.Embed(
                                    title="Please type what you would like to name your quiz.",
                                    colour=discord.Colour.orange()))
                                while 1:
                                    msg = await channel.history(limit=msg_limit).find(
                                        lambda m: str(m.author.id) == botname)
                                    if msg is not None:
                                        break
                                    msg_limit += 5

                            def checkName(message):
                                return message.channel == ctx.channel and message.author == ctx.author

                            try:
                                desiredName = await client.wait_for("message", timeout=20.0, check=checkName)

                                try:
                                    await msg.clear_reaction(checkMarks[0])
                                    await msg.clear_reaction(checkMarks[1])

                                    await msg.edit(embed=discord.Embed(
                                        title="Your quiz's name is currently **\"" + desiredName.content + "\"**. Is this correct?",
                                        colour=discord.Colour.purple()))
                                except:
                                    await channel.send(embed=discord.Embed(
                                        title="Your quiz's name is currently **\"" + desiredName.content + "\"**. Is this correct?",
                                        colour=discord.Colour.purple()))
                                    while 1:
                                        msg = await channel.history(limit=msg_limit).find(
                                            lambda m: str(m.author.id) == botname)
                                        if msg is not None:
                                            break
                                        msg_limit += 5

                                await msg.add_reaction(checkMarks[0])
                                await msg.add_reaction(checkMarks[1])

                                try:
                                    nameConfirmation = await client.wait_for("reaction_add", timeout=20.0,
                                                                             check=checkanswer)
                                    if nameConfirmation[0].emoji == checkMarks[0]:
                                        nameDesired = True
                                        quizname = desiredName.content

                                        createquiz()

                                        try:
                                            await msg.clear_reaction(checkMarks[0])
                                            await msg.clear_reaction(checkMarks[1])
                                        except:
                                            pass

                                        if privacySetting == "public":
                                            await msg.edit(embed=discord.Embed(
                                                title="Success! Your quiz set ID is " + unique_quizcode,
                                                colour=discord.Colour.green()))
                                        elif privacySetting == "private":
                                            await msg.edit(embed=discord.Embed(
                                                title="Quiz Key has been sent to your dm",
                                                colour=discord.Colour.green()))
                                            await author.send(embed=discord.Embed(
                                                title="Success! Your private quiz set ID is " + unique_quizcode,
                                                colour=discord.Colour.green()))
                                    elif nameConfirmation[0].emoji == checkMarks[1]:
                                        continue

                                except asyncio.TimeoutError:
                                    try:
                                        await msg.clear_reaction(checkMarks[0])
                                        await msg.clear_reaction(checkMarks[1])
                                    except:
                                        pass
                                    await msg.edit(embed=discord.Embed(
                                        title="You timed out!",
                                        colour=discord.Colour.red()))
                                    return

                            except asyncio.TimeoutError:
                                await msg.edit(embed=discord.Embed(
                                    title="You timed out!",
                                    colour=discord.Colour.red()))
                                return

                    elif changeName[0].emoji == checkMarks[1]:

                        createquiz()

                        try:
                            await msg.clear_reaction(checkMarks[0])
                            await msg.clear_reaction(checkMarks[1])
                        except:
                            pass

                        if privacySetting == "public":
                            await msg.edit(embed=discord.Embed(
                                title="Success! Your quiz set ID is " + unique_quizcode,
                                colour=discord.Colour.green()))
                        elif privacySetting == "private":
                            await author.send(embed=discord.Embed(
                                title="Success! Your private quiz set ID is " + unique_quizcode,
                                colour=discord.Colour.green()))

                except asyncio.TimeoutError:
                    try:
                        await msg.clear_reaction(checkMarks[0])
                        await msg.clear_reaction(checkMarks[1])
                    except:
                        pass
                    await msg.edit(embed=discord.Embed(
                        title="You timed out!",
                        colour=discord.Colour.red()))
                    return

            elif userAnswer[0].emoji == checkMarks[1]:
                try:
                    await msg.clear_reaction(checkMarks[0])
                    await msg.clear_reaction(checkMarks[1])
                except:
                    pass
                await msg.edit(embed=discord.Embed(
                    title="Got it. This quiz set won't be created.",
                    colour=discord.Colour.red()))
                return

        except asyncio.TimeoutError:
            try:
                await msg.clear_reaction(checkMarks[0])
                await msg.clear_reaction(checkMarks[1])
            except:
                pass
            await msg.edit(embed=discord.Embed(
                title="You timed out!",
                colour=discord.Colour.red()))
            return

    except asyncio.TimeoutError:
        await ctx.channel.send("You timed out!")
        return

    except:
        await ctx.channel.send("There was an issue reading your .csv file. Please retry the command.")


@client.command()
async def myQuiz(ctx):
    author = ctx.author
    channel = ctx.channel

    embed = discord.Embed(
        title="Quizzes made by " + str(author),

        color=discord.Colour.purple()
    )
    docs = client.quiz.find({"name": str(author.id)})
    for doc in docs:
        privacySetting = ""
        if doc["privacy"] == "private":
            privacySetting = " (private)"
        code = doc["_id"]
        name = doc["quizName"] + privacySetting
        embed.add_field(name=code, value=name, inline=False)
    await author.send(embed=embed)


@client.command()
async def delete(ctx, quizcode):
    msg_limit = 5
    try:
        channel = ctx.channel
        doc = client.quiz.find_one({"_id": quizcode})
        questions = doc["questions"]
        if doc["name"] != str(ctx.author.id):
            await channel.send(
                embed=discord.Embed(title="You are not authorized to delete this quiz", colour=discord.Colour.red()))
            return
        EmbedList = []
        Qnum = 1
        for iteration, row in enumerate(questions):
            #row = row.split("ȟ̵̢̨̤͕̔͊̓͒ͅ")
            for i in range(0, len(row)):
                if row[i] == '':
                    if i == 2:
                        row[i] = "None"
                    else:
                        row[i] = False
            for i in range(0, row.count(False)):
                row.remove(False)
            row[0] = str(Qnum)
            Qnum += 1
            embed = discord.Embed(
                title="Question " + row[0],
                description=row[1],

                colour=discord.Colour.blue()
            )
            if row[2] != "None":
                embed.set_image(url=row[2])
            for i, e in enumerate(emojis[:len(row[5:])]):
                if row[5 + i] == "TRUE":
                    row[5 + i] = "True"
                elif row[5 + i] == "FALSE":
                    row[5 + i] = "False"
                if ANSWERS[i] == row[3]:
                    embed.add_field(name=e, value=row[5 + i] + " (answer)")
                else:
                    embed.add_field(name=e, value=row[5 + i])
            embed.set_footer(text="You have " + row[4] + " seconds")
            EmbedList.append(embed)

        j = 0
        await channel.send(embed=EmbedList[j])
        while 1:
            msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
            if msg is not None:
                break
            msg_limit += 5
        await channel.send(
            embed=discord.Embed(
                title="Verify that this is the correct quiz. Navigate using the arrow keys and click the check mark when you're done checking.",
                colour=discord.Colour.light_gray()))
        await msg.add_reaction(arrows[0])
        await msg.add_reaction(arrows[1])
        await msg.add_reaction(checkMarks[0])

        def checkdirection(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '✔️' or str(reaction.emoji) == arrows[0] or str(
                reaction.emoji) == arrows[1])

        def checkRemoveDirection(payload):
            guild = client.get_guild(payload.guild_id)
            channel = guild.get_channel(payload.channel_id)
            reaction = payload.emoji.name
            return (payload.user_id == ctx.author.id and (str(reaction) == '✔️' or str(
                reaction) == arrows[0] or str(
                reaction) == arrows[1])) and msg.id == payload.message_id

        doneChecking = False

        while not doneChecking:
            pending_tasks = [client.wait_for('raw_reaction_remove', check=checkRemoveDirection),
                             client.wait_for('reaction_add', check=checkdirection)]
            done_tasks, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
            quizCheck = None
            for task in done_tasks:
                quizCheck = await task
            try:
                if quizCheck[0].emoji == arrows[0]:
                    j -= 1
                    if j < 0:
                        j = len(EmbedList) - 1
                    await msg.edit(embed=EmbedList[j])
                if quizCheck[0].emoji == arrows[1]:
                    j += 1
                    if j > len(EmbedList) - 1:
                        j = 0
                    await msg.edit(embed=EmbedList[j])
                if quizCheck[0].emoji == checkMarks[0]:
                    doneChecking = True
            except:
                if quizCheck.emoji.name == arrows[0]:
                    j -= 1
                    if j < 0:
                        j = len(EmbedList) - 1
                    await msg.edit(embed=EmbedList[j])
                if quizCheck.emoji.name == arrows[1]:
                    j += 1
                    if j > len(EmbedList) - 1:
                        j = 0
                    await msg.edit(embed=EmbedList[j])
                if quizCheck.emoji.name == checkMarks[0]:
                    doneChecking = True
        await msg.delete()
        while 1:
            msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
            if msg is not None:
                break
            msg_limit += 5
        await msg.edit(
            embed=discord.Embed(title="Is this the quiz set you wish to delete?", colour=discord.Colour.orange()))
        await msg.add_reaction(checkMarks[0])
        await msg.add_reaction(checkMarks[1])

        def checkanswer(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '✔️' or str(reaction.emoji) == '❌')

        try:
            userAnswer = await client.wait_for('reaction_add', timeout=20.0, check=checkanswer)
            if userAnswer[0].emoji == checkMarks[0]:
                client.quiz.delete_one({"_id": quizcode})
                client.quiz.update_one({"_id": "Key"}, {"$pull": {"Codes": quizcode}})
                try:
                    await msg.clear_reaction(checkMarks[0])
                    await msg.clear_reaction(checkMarks[1])
                    await msg.edit(embed=discord.Embed(
                        title="Success! " + quizcode + " has been deleted",
                        colour=discord.Colour.green()))
                except:
                    await msg.edit(embed=discord.Embed(
                        title="Success! " + quizcode + " has been deleted",
                        colour=discord.Colour.green()))
            elif userAnswer[0].emoji == checkMarks[1]:
                try:
                    await msg.clear_reaction(checkMarks[0])
                    await msg.clear_reaction(checkMarks[1])
                    await msg.edit(embed=discord.Embed(
                        title="Got it. Your quiz set won't be deleted.",
                        colour=discord.Colour.green()))
                    return
                except:
                    await msg.edit(embed=discord.Embed(
                        title="Got it. Your quiz set won't be deleted.",
                        colour=discord.Colour.green()))

        except asyncio.TimeoutError:
            try:
                await msg.clear_reaction(checkMarks[0])
                await msg.clear_reaction(checkMarks[1])
                await msg.edit(embed=discord.Embed(
                    title="You timed out!",
                    colour=discord.Colour.red()))
                return
            except:
                await msg.edit(embed=discord.Embed(
                    title="You timed out!",
                    colour=discord.Colour.red()))
    except:
        await ctx.channel.send(
            embed=discord.Embed(title="Invalid code entered!", colour=discord.Colour.red()))


@client.command()
async def help(ctx):
    channel = ctx.channel
    embed = discord.Embed(
        title="All Commands",

        color=discord.Colour.gold()
    )
    uploadCSV = "This command lets you begin the process of uploading a quiz csv to the database. \n You can find the quiz template at https://docs.google.com/spreadsheets/d/1H1Fg5Lw1hNMRFWkorHuAehRodlmHgKFM8unDjPZMnUg/edit#gid=196296521"
    embed.add_field(name="+upload", value=uploadCSV, inline=False)
    embed.add_field(name="+myQuiz", value="Direct messages you the keys and names of the quizzes you uploaded",
                    inline=False)
    run = "This command searches our database for a quiz of key QUIZKEY.  If QUIZKEY is valid, it will start the quiz."
    embed.add_field(name="+run QUIZKEY", value=run, inline=False)
    embed.add_field(name="+delete QUIZKEY", value="Asks you for confirmation then deletes this QUIZKEY from your bot.")
    embed.add_field(name="+edit QUIZKEY", value="Allows you to edit quizzes that you have created.")
    embed.add_field(name="Bot Invitation Link", value="https://bit.ly/2LsMwi6")
    embed.add_field(name="Note:",
                    value="Enabling the bot to manage messages, while not strictly required, helps prevent the bot from cluttering your channel history to provide you a more optimized experience.  Every other permission, however, is needed.")
    embed.add_field(name="Another Note:",
                    value="Only the run, delete, and edit commands require an argument to run properly.  Everything else can be run directly.")
    await channel.send(embed=embed)


@client.command()
async def edit(ctx, quizKey):
    msg_limit = 5
    MessageMan = True
    try:
        channel = ctx.channel
        doc = client.quiz.find_one({"_id": quizKey})
        if doc["name"] != str(ctx.author.id):
            await channel.send(
                embed=discord.Embed(title="You are not authorized to edit this quiz.", colour=discord.Colour.red()))
            return
        await channel.send(embed=discord.Embed(title="You are now editing " + quizKey + ": " + doc["quizName"],
                                               color=discord.Colour.green()))
        privacy = discord.Embed(title="This quiz's privacy is set to " + doc["privacy"],
                                description="Are you fine with this?",
                                color=discord.Colour.blue())
        await channel.send(embed=privacy)
        while 1:
            msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
            if msg is not None:
                break
            msg_limit += 5
        await msg.add_reaction(checkMarks[0])
        await msg.add_reaction(checkMarks[1])

        def setCheck(reaction, user):
            return user == ctx.author and (
                    str(reaction.emoji) == '✔️' or str(reaction.emoji) == '❌') and reaction.message == msg

        try:
            setting = await client.wait_for("reaction_add", timeout=10.0, check=setCheck)
            private = ""
            if doc["privacy"] == "private":
                private = "public"
            if doc["privacy"] == "public":
                private = "private"
            try:
                await msg.clear_reaction(checkMarks[0])
                await msg.clear_reaction(checkMarks[1])
            except:
                MessageMan = False

            if setting[0].emoji == checkMarks[1]:
                if MessageMan:
                    await msg.edit(
                        embed=discord.Embed(description="Would you like to switch this quiz to " + private + "?",
                                            color=discord.Colour.blue()))
                else:
                    await channel.send(
                        embed=discord.Embed(description="Would you like to switch this quiz to " + private + "?",
                                            color=discord.Colour.blue()))
                    while 1:
                        msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
                        if msg is not None:
                            break
                        msg_limit += 5
                await msg.add_reaction(checkMarks[0])
                await msg.add_reaction(checkMarks[1])
                try:
                    setting = await client.wait_for("reaction_add", timeout=10.0, check=setCheck)
                    if MessageMan:
                        await msg.clear_reaction(checkMarks[0])
                        await msg.clear_reaction(checkMarks[1])
                    if setting[0].emoji == checkMarks[0]:
                        client.quiz.update_one({"_id": quizKey},
                                               {"$set": {"privacy": private}})
                        await msg.edit(embed=discord.Embed(description="Alright! Changed privacy to " + private + "!",
                                                           color=discord.Colour.green()))
                    else:
                        await msg.edit(embed=discord.Embed(description="Not changing privacy.",
                                                           color=discord.Colour.green()))
                except asyncio.TimeoutError:
                    if MessageMan:
                        await msg.clear_reaction(checkMarks[0])
                        await msg.clear_reaction(checkMarks[1])
                    await msg.edit(embed=discord.Embed(
                        title="You timed out!",
                        colour=discord.Colour.red()))
                    return
            else:
                await msg.edit(embed=discord.Embed(description="Not changing privacy", color=discord.Colour.green()))
        except asyncio.TimeoutError:
            try:
                await msg.clear_reaction(checkMarks[0])
                await msg.clear_reaction(checkMarks[1])
            except:
                pass
            await msg.edit(embed=discord.Embed(
                title="You timed out!",
                colour=discord.Colour.red()))
            return
        question = discord.Embed(title="The quiz's name is " + doc["quizName"],
                                 description="Would you like to keep this?",
                                 color=discord.Colour.blue())
        await channel.send(embed=question)
        while 1:
            msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
            if msg is not None:
                break
            msg_limit += 5
        await msg.add_reaction(checkMarks[0])
        await msg.add_reaction(checkMarks[1])

        def validQuestion(message):
            if message.author != ctx.author:
                return False
            elif message.content == "":
                return False
            else:
                return True

        try:
            setting = await client.wait_for("reaction_add", timeout=10.0, check=setCheck)
            if MessageMan:
                await msg.clear_reaction(checkMarks[0])
                await msg.clear_reaction(checkMarks[1])
            if setting[0].emoji == checkMarks[1]:
                await msg.edit(
                    embed=discord.Embed(description="Write up what would you like to change the quiz name to.",
                                        color=discord.Colour.blue()))
                try:
                    question = await client.wait_for("message", timeout=20.0, check=validQuestion)
                    name = question.content
                    if MessageMan:
                        await msg.edit(
                            embed=discord.Embed(description="Would you like to set the quiz name to " + name + "?",
                                                color=discord.Colour.blue()))
                    else:
                        await channel.send(
                            embed=discord.Embed(description="Would you like to set the quiz name to " + name + "?",
                                                color=discord.Colour.blue()))
                        while 1:
                            msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
                            if msg is not None:
                                break
                            msg_limit += 5
                    await msg.add_reaction(checkMarks[0])
                    await msg.add_reaction(checkMarks[1])
                    try:
                        rxn = await client.wait_for("reaction_add", timeout=20, check=setCheck)
                        if MessageMan:
                            await msg.clear_reaction(checkMarks[0])
                            await msg.clear_reaction(checkMarks[1])
                        if rxn[0].emoji == checkMarks[0]:
                            client.quiz.update_one({"_id": quizKey},
                                                   {"$set": {"quizName": name}})
                            await msg.edit(embed=discord.Embed(description="Alright changed name to " + name + "!",
                                                               color=discord.Colour.green()))
                        else:
                            await msg.edit(embed=discord.Embed(description="Keeping name as " + doc["quizName"] + ".",
                                                               color=discord.Colour.green()))
                    except asyncio.TimeoutError:
                        if MessageMan:
                            await msg.clear_reaction(checkMarks[0])
                            await msg.clear_reaction(checkMarks[1])
                            await msg.edit(embed=discord.Embed(
                                title="You timed out!",
                                colour=discord.Colour.red()))
                            return
                except asyncio.TimeoutError:
                    await msg.edit(embed=discord.Embed(
                        title="You timed out!",
                        colour=discord.Colour.red()))
                    return
            else:
                await msg.edit(embed=discord.Embed(description="Keeping name as " + doc["quizName"] + ".",
                                                   color=discord.Colour.green()))
        except asyncio.TimeoutError:
            if MessageMan:
                await msg.clear_reaction(checkMarks[0])
                await msg.clear_reaction(checkMarks[1])
            await msg.edit(embed=discord.Embed(
                title="You timed out!",
                colour=discord.Colour.red()))
            return
        questions = doc["questions"]
        EmbedList = []
        Qnum = 1
        for iteration, row in enumerate(questions):
            #row = row.split("ȟ̵̢̨̤͕̔͊̓͒ͅ")
            for i in range(0, len(row)):
                if row[i] == '':
                    if i == 2:
                        row[i] = "None"
                    else:
                        row[i] = False
            for i in range(0, row.count(False)):
                row.remove(False)
            row[0] = str(Qnum)
            Qnum += 1
            embed = discord.Embed(
                title="Question " + row[0],
                description=row[1],

                colour=discord.Colour.blue()
            )
            if row[2] != "None":
                embed.set_image(url=row[2])
            for i, e in enumerate(emojis[:len(row[5:])]):
                if row[5 + i] == "TRUE":
                    row[5 + i] = "True"
                elif row[5 + i] == "FALSE":
                    row[5 + i] = "False"
                if ANSWERS[i] == row[3]:
                    embed.add_field(name=e, value=row[5 + i] + " (answer)")
                else:
                    embed.add_field(name=e, value=row[5 + i])
            embed.set_footer(text="You have " + row[4] + " seconds")
            EmbedList.append(embed)

        j = 0
        await channel.send(embed=EmbedList[j])
        while 1:
            msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
            if msg is not None:
                break
            msg_limit += 5
        await channel.send(
            embed=discord.Embed(
                description="These are the questions this quiz has. Navigate using the arrow keys and click the check mark when you're done checking.",
                colour=discord.Colour.light_gray()))
        await msg.add_reaction(arrows[0])
        await msg.add_reaction(arrows[1])
        await msg.add_reaction(checkMarks[0])

        def checkdirection(reaction, user):
            return user == ctx.author and (str(reaction.emoji) == '✔️' or str(reaction.emoji) == arrows[0] or str(
                reaction.emoji) == arrows[1])

        def checkRemoveDirection(payload):
            guild = client.get_guild(payload.guild_id)
            #channel = guild.get_channel(payload.channel_id)
            reaction = payload.emoji.name
            return (payload.user_id == ctx.author.id and (str(reaction) == '✔️' or str(
                reaction) == arrows[0] or str(
                reaction) == arrows[1])) and payload.message_id == msg.id

        doneChecking = False

        while not doneChecking:
            pending_tasks = [client.wait_for('raw_reaction_remove', check=checkRemoveDirection),
                             client.wait_for('reaction_add', check=checkdirection)]
            done_tasks, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
            quizCheck = None
            for task in done_tasks:
                quizCheck = await task
            try:
                if quizCheck[0].emoji == arrows[0]:
                    j -= 1
                    if j < 0:
                        j = len(EmbedList) - 1
                    await msg.edit(embed=EmbedList[j])
                if quizCheck[0].emoji == arrows[1]:
                    j += 1
                    if j > len(EmbedList) - 1:
                        j = 0
                    await msg.edit(embed=EmbedList[j])
                if quizCheck[0].emoji == checkMarks[0]:
                    doneChecking = True
            except:
                if quizCheck.emoji.name == arrows[0]:
                    j -= 1
                    if j < 0:
                        j = len(EmbedList) - 1
                    await msg.edit(embed=EmbedList[j])
                if quizCheck.emoji.name == arrows[1]:
                    j += 1
                    if j > len(EmbedList) - 1:
                        j = 0
                    await msg.edit(embed=EmbedList[j])
                if quizCheck.emoji.name == checkMarks[0]:
                    doneChecking = True
        await msg.delete()
        while 1:
            msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
            if msg is not None:
                break
            msg_limit += 5
        await msg.edit(
            embed=discord.Embed(description="Are you fine with these questions?", colour=discord.Colour.orange()))
        await msg.add_reaction(checkMarks[0])
        await msg.add_reaction(checkMarks[1])
        try:
            setting = await client.wait_for("reaction_add", timeout=15.0, check=setCheck)
            if MessageMan:
                await msg.clear_reaction(checkMarks[0])
                await msg.clear_reaction(checkMarks[1])
            if setting[0].emoji == checkMarks[1]:
                await msg.edit(embed=discord.Embed(description="Please upload the csv of this updated quiz",
                                                   colour=discord.Colour.orange()))

                def check(message):
                    return message.author == ctx.author and message.attachments[0].filename.endswith('.csv')

                try:
                    message = await client.wait_for('message', timeout=15.0, check=check)
                    await msg.delete()
                    file = message.attachments

                    if len(file) > 0 and file[0].filename.endswith('.csv'):
                        quiz = requests.get(file[0].url).content.decode("utf-8")
                        quiz = quiz.split("\n")
                        quiz = list(csv.reader(quiz))
                        EmbedList = []
                        # checks if you used the template
                        templatecheck = "Question No.,Question,Image URL,Answer (letter),Time,A,B,C,D,E,F,G,H,I,J"
                        if templatecheck not in ",".join(quiz[5]):
                            await channel.send(embed=discord.Embed(
                                title="Invalid .csv format! Please follow the template and follow the instructions listed. You can find the quiz template at https://docs.google.com/spreadsheets/d/1H1Fg5Lw1hNMRFWkorHuAehRodlmHgKFM8unDjPZMnUg/edit#gid=196296521",
                                colour=discord.Colour.red()))
                            return

                        Qnum = 1
                        for row in quiz[6:]:
                            if set(list(row)) == {''}:
                                continue
                            for i in range(0, len(row)):
                                if row[i] == "":
                                    if i == 2:
                                        row[i] = "None"
                                    else:
                                        row[i] = False
                            for i in range(0, row.count(False)):
                                row.remove(False)
                            row[0] = str(Qnum)
                            Qnum += 1
                            embed = discord.Embed(
                                title="Question " + row[0],
                                description=row[1],

                                colour=discord.Colour.blue()
                            )
                            if row[2] != "None":
                                embed.set_image(url=row[2])
                            # await channel.send(row[2])
                            for i, e in enumerate(emojis[:len(row[5:])]):
                                if row[5 + i] == "TRUE":
                                    row[5 + i] = "True"
                                elif row[5 + i] == "FALSE":
                                    row[5 + i] = "False"

                                # checks if you have a correct answer choice
                                validanswerchoice = False
                                if row[3].islower():
                                    await channel.send(
                                        "Answer choices are case sensitive! Please change your correct answer choice for question " +
                                        row[0])
                                    return
                                if row[3] in ANSWERS[:len(row[5:])]:
                                    validanswerchoice = True
                                if not validanswerchoice:
                                    await channel.send(
                                        "Question " + row[0] + " does not have a valid correct answer! (\"" + row[
                                            3] + "\") Please check the template for correct formatting.")
                                    return
                                if ANSWERS[i] == row[3]:
                                    embed.add_field(name=e, value=row[5 + i] + " (answer)")
                                else:
                                    embed.add_field(name=e, value=row[5 + i])

                                # checks if time is valid

                                if not row[4].isdigit():
                                    await channel.send(
                                        "Question " + row[0] + " does not have a valid time! (\"" + row[
                                            4] + "\")")
                                    return

                            embed.set_footer(text="You have " + row[4] + " seconds")
                            EmbedList.append(embed)

                        j = 0
                        await channel.send(embed=EmbedList[j])
                        while 1:
                            embed = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
                            if embed is not None:
                                break
                            msg_limit += 5
                        await embed.add_reaction(arrows[0])
                        await embed.add_reaction(arrows[1])
                        await embed.add_reaction(checkMarks[0])
                        await channel.send(
                            embed=discord.Embed(
                                title="These are the new questions you made. Please navigate through them using the arrow keys. Press the checkmark reaction once you're done checking",
                                colour=discord.Colour.dark_magenta()))
                        while 1:
                            msg = await channel.history(limit=msg_limit).find(lambda m: str(m.author.id) == botname)
                            if msg is not None:
                                break
                            msg_limit += 5
                        doneChecking = False

                        def Ncheckdirection(reaction, user):
                            return (user == message.author and (str(reaction.emoji) == '✔️' or str(
                                reaction.emoji) == arrows[0] or str(
                                reaction.emoji) == arrows[1])) and reaction.message == embed

                        def NcheckRemoveDirection(payload):
                            guild = client.get_guild(payload.guild_id)
                            channel = guild.get_channel(payload.channel_id)
                            reaction = payload.emoji.name
                            return (payload.user_id == ctx.author.id and (str(reaction) == '✔️' or str(
                                reaction) == arrows[0] or str(
                                reaction) == arrows[1])) and payload.message_id == embed.id

                        while not doneChecking:
                            pending_tasks = [client.wait_for('raw_reaction_remove', check=NcheckRemoveDirection),
                                             client.wait_for('reaction_add', check=Ncheckdirection)]
                            done_tasks, pending_tasks = await asyncio.wait(pending_tasks,
                                                                           return_when=asyncio.FIRST_COMPLETED)
                            quizCheck = None
                            for task in done_tasks:
                                quizCheck = await task
                            try:
                                if quizCheck[0].emoji == arrows[0]:
                                    j -= 1
                                    if j < 0:
                                        j = len(EmbedList) - 1
                                    await embed.edit(embed=EmbedList[j])
                                if quizCheck[0].emoji == arrows[1]:
                                    j += 1
                                    if j > len(EmbedList) - 1:
                                        j = 0
                                    await embed.edit(embed=EmbedList[j])
                                if quizCheck[0].emoji == checkMarks[0]:
                                    doneChecking = True
                            except:
                                if quizCheck.emoji.name == arrows[0]:
                                    j -= 1
                                    if j < 0:
                                        j = len(EmbedList) - 1
                                    await embed.edit(embed=EmbedList[j])
                                if quizCheck.emoji.name == arrows[1]:
                                    j += 1
                                    if j > len(EmbedList) - 1:
                                        j = 0
                                    await embed.edit(embed=EmbedList[j])
                                if quizCheck.emoji.name == checkMarks[0]:
                                    doneChecking = True
                    await embed.delete()
                    await msg.edit(embed=discord.Embed(title="Is this the updated quiz set you wish to create?",
                                                       colour=discord.Colour.purple()))
                    await msg.add_reaction(checkMarks[0])
                    await msg.add_reaction(checkMarks[1])
                    try:
                        setting = await client.wait_for("reaction_add", timeout=20.0, check=setCheck)
                        if MessageMan:
                            await msg.clear_reaction(checkMarks[0])
                            await msg.clear_reaction(checkMarks[1])
                        if setting[0].emoji == checkMarks[1]:
                            await msg.edit(embed=discord.Embed(description="Keeping the questions same",
                                                               colour=discord.Colour.green()))
                        else:
                            quiz = requests.get(file[0].url).content.decode("utf-8")
                            quiz = quiz.split("\n")
                            quiz = list(csv.reader(quiz))
                            client.quiz.update_one({"_id": quizKey},
                                                   {'$set': {"questions": []}})
                            for row in quiz[6:]:
                                if set(list(row)) == {''}:
                                    continue
                                y = row
                                #y = 'ȟ̵̢̨̤͕̔͊̓͒ͅ'.join(row)
                                client.quiz.update_one({"_id": quizKey},
                                                       {'$addToSet': {"questions": y}})
                            await msg.edit(embed=discord.Embed(description="Questions have been successfully updated",
                                                               colour=discord.Colour.green()))
                    except asyncio.TimeoutError:
                        if MessageMan:
                            await msg.clear_reaction(checkMarks[0])
                            await msg.clear_reaction(checkMarks[1])
                        await msg.edit(embed=discord.Embed(
                            title="You timed out!",
                            colour=discord.Colour.red()))
                        return
                except asyncio.TimeoutError:
                    await msg.edit(embed=discord.Embed(
                        title="You timed out!",
                        colour=discord.Colour.red()))
                    return
            else:
                await msg.edit(
                    embed=discord.Embed(description="Keeping the questions same", colour=discord.Colour.green()))
        except asyncio.TimeoutError:
            if MessageMan:
                await msg.clear_reaction(checkMarks[0])
                await msg.clear_reaction(checkMarks[1])
            await msg.edit(embed=discord.Embed(
                title="You timed out!",
                colour=discord.Colour.red()))
            return
        await channel.send(embed=discord.Embed(title="Finished editing", color=discord.Colour.green()))
    except:
        await ctx.channel.send(
            embed=discord.Embed(title="Invalid code or input entered!", colour=discord.Colour.red()))


# keep_alive.keep_alive()
client.run(token)
