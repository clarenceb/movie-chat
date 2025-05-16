from typing import List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, trim_messages
from langchain.callbacks.base import BaseCallbackHandler

def set_color(color=''):
    color_codes = {
        'red': "\033[91m",
        'green': "\033[92m",
        'yellow': "\033[93m",
        'blue': "\033[94m",
        'magenta': "\033[95m",
        'cyan': "\033[96m",
    }
    return color_codes.get(color, "\033[0m")  # Default to reset

def print_color(color=''):
    print(set_color(color))

def debug_chat_history(messages: List[HumanMessage | AIMessage | SystemMessage], truncate_length=200):
    print(f"\n{set_color('yellow')}########################## Chat history ###################################")
    print(f"{set_color('green')}Chat history message count:{set_color()}{len(messages)}")
    for i, message in enumerate(messages):
        message_type = message.__class__.__name__
        if len(message.content) > truncate_length:
            content_preview = f"{message.content[:truncate_length]}{set_color('red')}...(truncated){set_color()}"
        else:
            content_preview = message.content
        print(f"{set_color('green')}{message_type}({i+1}):{set_color()} {content_preview}")
    print(f"{set_color('yellow')}############################################################################\n")
    print_color()

class DebugCallbackHandler(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs):
        output = response.generations[0][0].text
        truncate_length=200
        print(f"\n{set_color('yellow')}########################## Callback - LLM End ###################################{set_color()}")
        if len(output) > truncate_length:
            content_preview = f"{output[:truncate_length]}{set_color('red')}...(truncated){set_color()}"
        else:
            content_preview = output
        print(f"{set_color('green')}response.generations[0][0].text:\n{set_color()} {content_preview}")
        print(f"{set_color('yellow')}############################################################################{set_color()}\n")
