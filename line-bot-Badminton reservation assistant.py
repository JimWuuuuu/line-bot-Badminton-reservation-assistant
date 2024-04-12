from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime, timedelta
import time
import schedule
import threading

app = Flask(__name__)

# 設定 Channel Access Token 和 Channel Secret
CHANNEL_ACCESS_TOKEN = 'UaowmmTPRWJPdF6x0FYS0smm1f71UHhuPTpc0sztFFbWKuef0z16PiTtk6/uFPW5vExL83OYngxn81tC8RkHtT8cTn2cdhfzVUkMU8EVmYiFAWJB/aOmx32LW07UC0a2F8NSnp3hEZcQ+kpdvflN8wdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'adf5d04f2c6e900b49b949fc991b06fc'

# 初始化 LineBotApi 和 WebhookHandler
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 記錄使用者是否固定參與本週活動的字典，格式為 {user_id: True/False}
weekly_fixed_participation = {}

# 記錄每週固定參與的人員，格式為 [user_id1, user_id2, ...]
fixed_participants = []

# 記錄單次參與本週活動的人員，格式為 {user_id: True/False}
weekly_participation = {}

# 記錄這禮拜有要打的人員，格式為 [user_id1, user_id2, ...]
this_week_participants = []

def refresh_participant_list():
    participant_names = get_participant_names()
    line_bot_api.broadcast(
        TextSendMessage(text=f"這禮拜打羽球的人有：{participant_names}\n\n"
                            f"請記得給錢一人200元!!名單已刷新。"
        )
    )
    global this_week_participants
    # 在這個函數中更新參與名單
    # 確保固定參與者保持不變
    for user_id in fixed_participants:
        if user_id not in weekly_fixed_participation:
            weekly_fixed_participation[user_id] = True

    # 清除單次參與者名單
    weekly_participation.clear()

    # 更新這禮拜有要打的人員
    this_week_participants = [user_id for user_id, participation in weekly_participation.items() if participation]

def ask_for_participants():
    fixed_participant_names = get_fixed_participant_names()
    line_bot_api.broadcast(
        TextSendMessage(text=f"目前固定班底名單有：{fixed_participant_names}\n\n"
                            f"請於今天晚上10:00前回覆「打」、「pass」來確認這禮拜是否要打羽球。"
        )
    )

def notify_participants():
    participant_names = get_participant_names()
    line_bot_api.broadcast(
        TextSendMessage(text=f"明天打羽球的人員有：{participant_names}\n\n"
        )
    )

# 設定每週六下午3:00詢問名單的定時任務
schedule.every().saturday.at("15:00").do(ask_for_participants)
# 在週六晚上10點統整名單並通知本週參與者
schedule.every().saturday.at("22:00").do(notify_participants)
# 設定每週日晚上10:00刷新名單的定時任務
schedule.every().sunday.at("22:00").do(refresh_participant_list)



# 定義一個函數來在後台運行定時任務
def run_schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

# 在另一個線程中運行定時任務
schedule_thread = threading.Thread(target=run_schedule_thread)
schedule_thread.start()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text

    if message_text in ["打爛", "打", "確定打"]:
        weekly_fixed_participation[user_id] = True
        weekly_participation[user_id] = True
        this_week_participants.append(user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"{get_weekly_participant_message(user_id)}這週要打！")
        )
    elif message_text in ["pass", "不打", "烙跑","Pass"]:
        if user_id in weekly_participation:
            weekly_participation[user_id] = False
            this_week_participants.remove(user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"{get_weekly_participant_message(user_id)}這週要烙跑！")
            )
        elif user_id in fixed_participants:
             # 如果是固定班底且在刷新名單前回覆了 "pass"，則將其從本週參與者中移除
             this_week_participants.remove(user_id)
             line_bot_api.reply_message(
                 event.reply_token,
                 TextSendMessage(text=f"{get_weekly_participant_message(user_id)}媽的固定班底還敢烙跑！")
            )    
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="你還沒設定是否參加本週活動！")
            )
    elif message_text in ["每個禮拜都打", "每周都參加","固定班底"]:
        if user_id not in fixed_participants:
            fixed_participants.append(user_id)
            weekly_fixed_participation[user_id] = True
            weekly_participation[user_id] = True
            this_week_participants.append(user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"恭喜 {get_display_name(user_id)} 成為固定班底！")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="你已經是固定班底了！")
            )
    elif message_text == "取消固定班底":
        if user_id in fixed_participants:
            fixed_participants.remove(user_id)
            weekly_fixed_participation[user_id] = False
            if user_id in this_week_participants:
                this_week_participants.remove(user_id)  # 使用 .remove() 方法移除用戶
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"已取消 {get_display_name(user_id)} 的固定班底！")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="你不是固定班底，無法取消！")
            )
    elif message_text in ["這禮拜有誰", "這禮拜誰要打","這禮拜有誰要打"]:
        # 計算本週禮拜日的日期
        this_sunday = datetime.now() + timedelta(days=(6 - datetime.now().weekday()))
        # 取得本週打球的參與者名單
        participant_names = get_participant_names()
        # 回覆訊息，顯示本週禮拜日的日期和參與者名單
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"這週{this_sunday.strftime('(%m/%d)')}晚上10:00要打的人有：{participant_names}")
        )
    elif message_text == "固定班底有誰":
        fixed_participant_names = get_fixed_participant_names()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"目前的固定班底有：{fixed_participant_names}")
        )
    elif message_text == "重開機":
        reset_all_lists()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="名單已重置！")
        )


def get_participant_names():
    unique_participant_ids = set(this_week_participants)
    participant_names = []
    for user_id in unique_participant_ids:
        profile = line_bot_api.get_profile(user_id)
        participant_names.append(profile.display_name)
    return ', '.join(participant_names)


def get_fixed_participant_names():
    fixed_participant_names = []
    for user_id in fixed_participants:
        profile = line_bot_api.get_profile(user_id)
        fixed_participant_names.append(profile.display_name)
    return ', '.join(fixed_participant_names)

def get_weekly_participant_message(user_id):
    display_name = get_display_name(user_id)
    if user_id in fixed_participants:
        return f"{display_name} ，"
    elif user_id in weekly_fixed_participation and weekly_fixed_participation[user_id]:
        return f"{display_name} ，"
    else:
        return f"{display_name}，"

def get_display_name(user_id):
    profile = line_bot_api.get_profile(user_id)
    return profile.display_name

def reset_all_lists():
    global weekly_fixed_participation, fixed_participants, weekly_participation, this_week_participants
    weekly_fixed_participation = {}
    fixed_participants = []
    weekly_participation = {}
    this_week_participants = []


if __name__ == "__main__":
    app.run()
