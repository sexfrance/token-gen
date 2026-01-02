from dataclasses import dataclass, field
from collections import deque
from typing import Optional, Tuple
from time import time
from threading import Event

@dataclass
class AccountContext:
    fingerprint: str
    username: str
    password: str
    email: str
    birthday: Tuple[int, int, int]
    proxy: str

    captcha_key: Optional[str] = None
    token: Optional[str] = None
    upn: Optional[str] = None
    
@dataclass
class TitleBarStats:
    token_generated: int = 0
    ev_tokens: int = 0
    invalid_tokens: int = 0
    locked_tokens: int = 0
    
    consecutive_failures: int = 0
    soft_flag_hits: int = 0
    stop_event: Event = field(default_factory=Event, repr=False)


    start_time: float = field(default_factory=time)
    _token_times: deque = field(default_factory=deque, init=False, repr=False)

    def mark_valid(self):
        self.token_generated += 1
        self.consecutive_failures = 0
        self.soft_flag_hits = 0
        self._mark_time()

    def mark_invalid(self):
        self.invalid_tokens += 1
        self.consecutive_failures += 1
        self.soft_flag_hits += 1
        self._mark_time()

    def mark_locked(self):
        self.locked_tokens += 1
        self.consecutive_failures += 1
        self.soft_flag_hits += 1
        self._mark_time()

    def _mark_time(self):
        now = time()
        self._token_times.append(now)
        while self._token_times and now - self._token_times[0] > 60:
            self._token_times.popleft()

    def should_stop(self) -> bool:
        if self.consecutive_failures >= 10:
            return True

        if self.soft_flag_hits >= 5:
            return True

        total = self.invalid_tokens + self.locked_tokens + self.ev_tokens
        if total >= 20:
            bad_ratio = (self.invalid_tokens + self.locked_tokens) / total
            if bad_ratio >= 0.8:
                return True

        return False

    @property
    def tokens_per_minute(self) -> float:
        elapsed_seconds = max(time() - self.start_time, 1)
        elapsed_minutes = elapsed_seconds / 60
        return round(self.token_generated / elapsed_minutes, 2)



    @property
    def time_elapsed(self) -> int:
        return int(time() - self.start_time)
    

    def format_title(self) -> str:
        m, s = divmod(self.time_elapsed, 60)
        return (
            f"??? │ "
            f"Gen: {self.token_generated} │ "
            f"EV: {self.ev_tokens} │ "
            f"Inv: {self.invalid_tokens} │ "
            f"Lock: {self.locked_tokens} │ "
            f"CPM: {self.tokens_per_minute} │ "
            f"Time: {m:02}:{s:02}"
        )