import sys
from datetime import datetime
from pathlib import Path

class Logger:
    def __init__(self, log_dir="logs", prefix="v9"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.prefix = prefix

        # 초기 로그 파일 생성
        self.rotate_log_file(initial=True)

    def info(self, message):
        self._log("INFO", message)

    def error(self, message):
        self._log("ERROR", message)

    def warning(self, message):
        self._log("WARN", message)

    def rotate_log_file(self, initial=False):
        """새로운 로그 파일 생성 (사이클 종료 시 호출)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = self.log_dir / f"{self.prefix}_{timestamp}.log"

        if not initial:
            # 초기 생성이 아닐 때만 로그 메시지 출력
            self.info(f"[LOG] 새 로그 파일: {self.log_file.name}")

        return self.log_file

    def _log(self, level, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}"

        # 콘솔 출력
        if level == "ERROR":
            print(f"\033[91m{log_line}\033[0m", file=sys.stderr)
        elif level == "WARN":
            print(f"\033[93m{log_line}\033[0m")
        else:
            print(log_line)

        # 파일 저장
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except:
            pass

# 싱글톤 패턴으로 사용 가능하도록 인스턴스 생성
logger = Logger()
