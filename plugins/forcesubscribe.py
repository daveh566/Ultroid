# Ultroid - UserBot
# Copyright (C) 2021 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.


"""
✘ Commands Available -

• `{i}fsub <chat username><id>`
    Enable ForceSub in Used Chat !

• `{i}checkfsub`
    Check/Get Active ForceSub Setting of Used Chat.

• `{i}remfsub`
    Remove ForceSub from Used Chat !

    Note - You Need to be Admin in Both Channel/Chats
        in order to Use ForceSubscribe.
"""


import re

from pyUltroid.functions.forcesub_db import *
from telethon.errors.rpcerrorlist import UserNotParticipantError
from telethon.tl.custom import Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.types import ChannelParticipantBanned

from . import *

CACHE = {}


@ultroid_cmd(pattern="fsub ?(.*)", admins_only=True, groups_only=True)
async def addfor(e):
    match = e.pattern_match.group(1)
    if not match:
        return await eod(e, "Give Channel where you want User to Join !")
    if match.startswith("@"):
        ch = match
    else:
        try:
            ch = int(match)
        except BaseException:
            return await eod(e, "Give Correct Channel Username or id")
    try:
        match = (await e.client.get_entity(ch)).id
    except BaseException:
        return await eod(e, "Give Correct Channel Username or id")
    if not str(match).startswith("-100"):
        match = int("-100" + str(match))
    add_forcesub(e.chat_id, match)
    await eor(e, "Added ForceSub in This Chat !")


@ultroid_cmd(pattern="remfsub$")
async def remor(e):
    res = rem_forcesub(e.chat_id)
    if not res:
        return await eod(e, "ForceSub was not Active in this Chat !")
    await eor(e, "Removed ForceSub...")


@ultroid_cmd(pattern="checkfsub$")
async def getfsr(e):
    res = get_forcesetting(e.chat_id)
    if not res:
        return await eod(e, "ForceSub is Not Active In This Chat !")
    cha = await e.client.get_entity(int(res))
    await eor(e, f"**ForceSub Status** : `Active`\n- **{cha.title}** `({res})`")


@in_pattern("fsub ?(.*)")
@in_owner
async def fcall(e):
    match = e.pattern_match.group(1)
    spli = match.split("_")
    user = await ultroid_bot.get_entity(int(spli[0]))
    cl = await ultroid_bot.get_entity(int(spli[1]))
    text = f"Hi [{user.first_name}](tg://user?id={user.id}), You Need to Join"
    text += f" {cl.title} in order to Chat in this Group."
    if not cl.username:
        el = (await ultroid_bot(ExportChatInviteRequest(cl))).link
    else:
        el = "https://t.me/" + cl.username
    res = [
        await e.builder.article(
            title="forcesub",
            text=text,
            buttons=[
                [Button.url(text="Join Channel", url=el)],
                [Button.inline("Unmute Me", data=f"unm_{match}")],
            ],
        )
    ]
    await e.answer(res)


@callback(re.compile("unm_(.*)"))
async def diesoon(e):
    match = (e.data_match.group(1)).decode("UTF-8")
    spli = match.split("_")
    if e.sender_id != int(spli[0]):
        return await e.answer("This Message is Not for You", alert=True)
    try:
        await ultroid_bot(GetParticipantRequest(int(spli[1]), int(spli[0])))
    except UserNotParticipantError:
        return await e.answer(
            "Please Join That Channel !\nThen Click This Button !", alert=True
        )
    await ultroid_bot.edit_permissions(
        e.chat_id, int(spli[0]), send_messages=True, until_date=None
    )
    await e.edit("Thanks For Joining ! ")


@ultroid_bot.on(events.NewMessage())
async def cacheahs(ult):
    if udB.get("FORCESUB"):
        user = await ult.get_sender()
        if not get_forcesetting(ult.chat_id) or user.bot:
            return
        joinchat = get_forcesetting(ult.chat_id)
        try:
            co = CACHE[ult.chat_id]
            count = co[user.id]["count"] + 1
            CACHE.update({ult.chat_id: {user.id: {"count": count}}})
            if count == 10:
                co[user.id]["count"] = 0
            return
        except KeyError:
            count = 1
            try:
                chat = CACHE[ult.chat_id]
                chat.update({user.id: {"count": count}})
            except KeyError:
                CACHE.update({ult.chat_id: {user.id: {"count": count}}})
        try:
            part = await ultroid_bot.get_permissions(int(joinchat), user.id)
            if isinstance(part, ChannelParticipantBanned) and part.participant.left:
                raise UserNotParticipantError(None)
            return
        except UserNotParticipantError:
            pass
        await ultroid_bot.edit_permissions(ult.chat_id, user.id, send_messages=False)
        res = await ultroid_bot.inline_query(
            asst.me.username, f"fsub {user.id}_{joinchat}"
        )
        await res[0].click(ult.chat_id, reply_to=ult.id)
