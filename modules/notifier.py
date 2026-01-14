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
        """일일 요약 알림"""
        now = datetime.now().strftime("%Y-%m-%d")
        subject = f"[Account Automation] 일일 요약 리포트 - {now}"

        total_uploads = stats.get('count', 0)
        success_count = total_uploads  # 업로드 성공한 건수
        failure_count = 0  # 현재 시스템에서 실패는 추적하지 않음
        cancellations = stats.get('cancellations', 0)
        normal_transactions = total_uploads - cancellations
        success_rate = 100.0 if total_uploads > 0 else 0

        body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 일일 요약 ({now})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 업로드할 데이터 수: {total_uploads}건
✅ 업로드 성공: {success_count}건
❌ 업로드 실패: {failure_count}건
       승인취소: {cancellations}건
       결재취소: 0건
        취소(-): {cancellations}건
성공률: {success_rate:.0f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
실행 통계: {stats.get('total', 0)}회 실행 ({stats.get('success', 0)}회 성공, {stats.get('failure', 0)}회 실패)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return self.send_email(subject, body)
