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
CHANNEL_ACCESS_TOKEN = '0OHIdiUtl9Z9DsHIaOikgay3Z//Usjv0quMJqbeNdM73T9elpisz7NlxiXBtj+tUvExL83OYngxn81tC8RkHtT8cTn2cdhfzVUkMU8EVmYh7EWd9dctK1fUT4DL4ueXcMUhokw0hPf/TF+BB86IvxAdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'b1cb784730e763b483e953ec0ea5cc80'

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
    fixed_participant_names = get_fixed_participant_names()
    line_bot_api.broadcast(
        TextSendMessage(text=f"這禮拜打羽球的人有：{participant_names}\n\n"
                             f"請記得給錢，一人200元，給劻!!名單已刷新。"
        )
    )
    global this_week_participants
    # 清除單次參與者名單
    weekly_participation.clear()
    this_week_participants.clear()
    
    # 更新這禮拜有要打的人員
    this_week_participants += [user_id for user_id, participation in weekly_participation.items() if participation]

    # 將固定參與者加入這禮拜有要打的人員
    this_week_participants += fixed_participants.copy()

def ask_for_participants(group_id):
    fixed_participant_names = get_fixed_participant_names()
    participant_names = get_participant_names()
    line_bot_api.push_message(
        group_id,
        TextSendMessage(text=f"固定班底名單有：{fixed_participant_names}\n\n"
                             f"目前明天打羽球的人員有：{participant_names}\n\n"
                             f"請於今天晚上10:00前回覆「打」、「pass」來確認這禮拜是否要打羽球。"
        )
    )

def notify_participants():
    participant_names = get_participant_names()
    line_bot_api.broadcast(
        TextSendMessage(text=f"統計結束，明天打羽球的人員有：{participant_names}\n\n"
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
            TextSendMessage(text=f"這週{this_sunday.strftime('(%m/%d)')}晚上08:00要打的人有：{participant_names}")
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
    elif message_text.startswith("修改人員"):
        # 解析指令格式，格式為：修改參與人員 [名稱] [狀態]
        parts = message_text.split(" ")
        if len(parts) == 3:
            name = parts[1]
            status = parts[2]
            modify_participant_status(name, status, event)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="指令格式錯誤！請輸入：修改人員 [名稱] [狀態]")
            )
    else:
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="無效的指令！請重新輸入。")
    )


def modify_participant_status(name, status, event):
    # 根據名稱找到對應的使用者 ID
    user_id = find_user_id_by_name(name)
    if user_id:
        # 根據狀態修改參與者的狀態
        if status in ["打", "確定打"]:
            weekly_fixed_participation[user_id] = True
            weekly_participation[user_id] = True
            if user_id not in this_week_participants:
                this_week_participants.append(user_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"{get_weekly_participant_message(user_id)}這週要打！")
            )
        elif status in ["pass", "不打", "烙跑", "Pass"]:
            if user_id in weekly_participation:
                weekly_participation[user_id] = False
                if user_id in this_week_participants:
                    this_week_participants.remove(user_id)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"{get_weekly_participant_message(user_id)}這週要烙跑！")
                )
            elif user_id in fixed_participants:
                if user_id in this_week_participants:
                    this_week_participants.remove(user_id)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"{get_weekly_participant_message(user_id)}媽的固定班底還敢烙跑！")
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="該使用者並未參與本週活動！")
                )
        elif status == "固定班底":
            if user_id not in fixed_participants:
                fixed_participants.append(user_id)
                weekly_fixed_participation[user_id] = True
                weekly_participation[user_id] = True
                if user_id not in this_week_participants:
                    this_week_participants.append(user_id)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"恭喜 {get_display_name(user_id)} 成為固定班底！")
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="該使用者已經是固定班底！")
                )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="無效的狀態！狀態應該為：打、不打、烙跑、固定班底")
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="找不到該使用者！")
        )




def find_user_id_by_name(name):
    # 根據名稱找到對應的使用者 ID
    for user_id in weekly_participation.keys():
        profile = line_bot_api.get_profile(user_id)
        if profile.display_name == name:
            return user_id
    return None


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
