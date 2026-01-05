import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from core.logger import logger
from utils.config import NOTIFICATION_CONFIG

class NotifierModule:
    """이메일 알림 발송 모듈"""
    
    def __init__(self):
        self.config = NOTIFICATION_CONFIG.get("email", {})
        self.enabled = self.config.get("enabled", False)
        self.smtp_server = self.config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = self.config.get("smtp_port", 587)
        self.sender = self.config.get("sender", "")
        self.sender_password = self.config.get("sender_password", "")
        self.recipient = self.config.get("recipient", "")

    def send_email(self, subject, body):
        """이메일 발송 실행"""
        if not self.enabled:
            logger.info("ℹ️ 이메일 알림이 비활성화되어 있습니다.")
            return False
            
        if not all([self.sender, self.sender_password, self.recipient]):
            logger.warning("⚠️ 이메일 설정이 누락되어 발송을 건너뜁니다.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = self.recipient
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender, self.recipient, text)
            server.quit()
            
            logger.info(f"✅ 이메일 알림 발송 완료: {subject}")
            return True
        except Exception as e:
            logger.error(f"❌ 이메일 발송 실패: {e}")
            return False

    def send_error_notification(self, error_msg, trace=""):
        """에러 발생 알림"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = f"[Account Automation] 에러 발생 알림 - {now}"
        body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 자동화 프로그램 에러 발생
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

발생 시간: {now}
에러 메시지: 
{error_msg}

상세 정보:
{trace if trace else '정보 없음'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
본 메일은 시스템에 의해 자동 발송되었습니다.
"""
        return self.send_email(subject, body)

    def send_summary_notification(self, stats):
        """일일 요약 알림 (향후 확장용)"""
        now = datetime.now().strftime("%Y-%m-%d")
        subject = f"[Account Automation] 일일 요약 리포트 - {now}"
        body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 일일 실행 요약 ({now})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

총 실행 횟수: {stats.get('total', 0)}회
성공: {stats.get('success', 0)}회
실패: {stats.get('failure', 0)}회
총 처리 데이터: {stats.get('count', 0)}건

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return self.send_email(subject, body)
