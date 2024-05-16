# line-bot-Badminton-reservation-assistant
我是羽球同好會專用小助理(shaking hand)

以下是我的使用說明書！

歡迎使用打羽球活動通知機器人！這個機器人可以協助您組織羽球活動並通知參與者。

功能簡介

這是一個基於 LINE Messaging API 的羽球活動管理機器人，旨在自動化管理每週的羽球活動參與者名單。主要功能包括定時提醒、名單統整、固定班底管理和參與狀態更新。

功能特點

定時提醒：每週六下午3:00會提醒使用者回覆是否參加本週的羽球活動。

名單統整：每週六晚上10:00會統整參與者名單，並在週日晚上10:00刷新名單。

固定班底：使用者可以設定成為固定參與者，每週無需回覆即自動列入參與名單。

烙跑功能：使用者可以回覆 "pass" 表示本週不參加活動，包括固定參與者。

使用說明

指令說明

設定參與狀態

回覆「打」或「確定打」來確認本週參加活動。

回覆「pass」、「不打」、「烙跑」來表示本週不參加活動。

固定班底設定
回覆「每個禮拜都打」或「每周都參加」來設定成為固定班底，無需每週回覆。

查詢參與名單
回覆「這禮拜有誰」或「這禮拜誰要打」來查詢本週參與者名單。

取消參加
若已回覆「打」但後來無法參加，可回覆「pass」來取消參加。

固定班底查詢
回覆「固定班底有誰」來查詢目前的固定班底名單。

重置名單
回覆「重開機」來重置所有名單及設定。

修改參與人員
回覆「修改人員 [名稱] [狀態]」來修改某位使用者的參與狀態。例如：「修改人員 Rex 打」、「修改人員 John pass」、「修改人員 Lily 固定班底」。


操作範例

若你每週都想參加活動，請回覆「每個禮拜都打」。

若你這週要參加活動，請回覆「打」。

若你這週不能參加活動，請回覆「pass」。

若你想查詢這週參加活動的人員，請回覆「這禮拜有誰」。

若你是管理員且需要修改某人的狀態，請回覆「修改人員 [名稱] [狀態]」，例如：「修改人員 Rex 打」。


使用注意事項

請確保所有指令輸入正確，包括名稱和狀態。

參與狀態的有效值包括：「打」、「確定打」、「pass」、「不打」、「烙跑」、「固定班底」。

若遇到問題或需要重置系統，請使用「重開機」指令。



技術說明

環境配置

安裝 Python 和相關套件

安裝 Flask 用於建立 Web 伺服器。

安裝 LINE Bot SDK 用於與 LINE 平台互動。

安裝 Schedule 用於定時任務管理。

設定 Channel Access Token 和 Channel Secret

CHANNEL_ACCESS_TOKEN = '0OHIdiUtl9Z9DsHIaOikgay3Z//Usjv0quMJqbeNdM73T9elpisz7NlxiXBtj+tUvExL83OYngxn81tC8RkHtT8cTn2cdhfzVUkMU8EVmYh7EWd9dctK1fUT4DL4ueXcMUhokw0hPf/TF+BB86IvxAdB04t89/1O/w1cDnyilFU='

CHANNEL_SECRET = 'b1cb784730e763b483e953ec0ea5cc80'

在 LINE Developer 平台取得 Channel Access Token 和 Channel Secret，並在程式碼中設定。


運行伺服器

使用 ngrok 來將本地伺服器暴露給互聯網，以便接收 LINE 的 Webhook 請求。

程式碼結構

app.py：主程式，包含所有邏輯和功能實現。

refresh_participant_list()：定期刷新參與者名單。

ask_for_participants()：定期詢問使用者是否參加本週活動。

notify_participants()：通知參與者名單。

modify_participant_status()：修改參與者狀態。

find_user_id_by_name()：根據名稱找到對應的使用者 ID。

get_participant_names()：獲取本週參與者名單。

get_fixed_participant_names()：獲取固定班底名單。

get_weekly_participant_message()：生成每週參與訊息。

get_display_name()：獲取使用者顯示名稱。

reset_all_lists()：重置所有名單和設定。


運行步驟

安裝並配置好 Python 環境。

確保已經安裝 Flask、line-bot-sdk 和 schedule 模塊。

確保 CHANNEL_ACCESS_TOKEN 和 CHANNEL_SECRET 已正確設置。


運行 app.py：

python app.py

ngrok http 5000


在 LINE Developer 平台設定 Webhook URL 為 ngrok 提供的 URL，加上 /callback 路徑。

開始使用機器人，依照上述指令操作。



聯絡我們

如有任何問題或建議，請不要聯絡我們！
