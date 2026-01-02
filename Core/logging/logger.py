from Core.NexusColors.color import NexusColor
import threading                                                                                                                                                                                                                                                                    ; VATOS = threading.Semaphore(28) 

class VatosLogger:
    
    def __init__(self, config):
        self.LC = f"{NexusColor.PURPLE}[{NexusColor.LIGHTBLACK}VATOS{NexusColor.PURPLE}] "
        self.config = config
        
    def log(self, msg: str) -> None:
        print(self.LC + NexusColor.LIGHTBLACK + msg)

    def log_token(self, msg: str, token: str) -> None:
        if self.config["logs"]["censor_token"]:
            parts = token.split(".")

            if len(parts) == 3:
                part1, part2, part3 = parts

                censored_part1 = part1[:6] + "******"
                censored_part3 = "*******" + part3[-6:]

                token = f"{censored_part1}.{part2}.{censored_part3}"
    
        print(self.LC + NexusColor.LIGHTBLACK + msg + token)