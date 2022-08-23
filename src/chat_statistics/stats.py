import json
from collections import Counter, defaultdict
from ctypes import Union
from pathlib import Path
from re import T
from typing import Union

import arabic_reshaper
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
from hazm import *
from loguru import logger
from src.data import DATA_DIR
from src.utils.io import read_file
from wordcloud import WordCloud


class ChatStatistics:
    """Generates chat statistics from a telegram chat json file
    """
    def __init__(self, chat_json: Union[str, Path]) :
        """
        :param chat_json: path to telegram export json file
        """
        # load chat data
        logger.info(f"loading chat data from {chat_json}")
        with open(chat_json) as f:
            self.chat_data = json.load(f)

        self.normalizer = Normalizer()

        # load stopwords
        logger.info('Loadind stopwords ')
        stop_words = open(DATA_DIR / 'stopwords.txt').readlines()
        stop_words = map(str.strip, stop_words)
        self.stop_words = set(map(self.normalizer.normalize, stop_words))

    @staticmethod
    def rebuild_msg(sub_messages):
            msg_text = ''
            for sub_msg in sub_messages:
                if isinstance(sub_msg, str):
                    msg_text += sub_msg
                elif 'text' in sub_msg:
                    msg_text += sub_msg['text']
            return msg_text

    def msg_has_question(self, msg):
        """Checks if a message has a question

        Args:
            msg: message to check
        """
        if not isinstance(msg['text'], str):
            msg['text'] = self.rebuild_msg(msg['text'])

        sentences = sent_tokenize(msg['text'])
        for sentence in sentences:
            if ('؟' not in sentence) and ('?' not in sentence):
                continue

            return True

    def get_top_users(self, top_n: int = 10) -> dict:
        """Gets top n users from the chat

        Args:
            top_n (int, optional): numbet of users to get. Defaults to 10.

        Returns:
            dict: dict of top users
        """
        # check messages for questions
        is_question = defaultdict(bool)
        for msg in self.chat_data['messages']:
            if not isinstance(msg['text'], str):
                msg['text'] = self.rebuild_msg(msg['text'])

            sentences = sent_tokenize(msg['text'])
            for sentence in sentences:
                if ('؟' not in sentence) and ('?' not in sentence):
                    continue

                is_question[msg['id']] = True
                break
        # get top users based on replying to questions from others
        logger.info('getting top users...')
        users = []
        for msg in self.chat_data['messages']:
            if not msg.get('reply_to_message_id'):
                continue
            if is_question[msg['reply_to_message_id']] is False:
                continue
            users.append(msg['from'])

        return dict(Counter(users).most_common(top_n))

    def generate_word_cloud(self, output_dir: Union[str, Path],
    width: int = 1200, height: int = 600,
    background_color: str ='white',
    ):
        """_summary_

        Args:
            output_dir (Path_): path to output directory for word cloud image
        """
        text_content = ''
        logger.info('Loading text content')
        for msg in self.chat_data['messages']:
            if type(msg['text']) is str:
                tokens = word_tokenize(msg['text'])
                tokens = list(filter(lambda item: item not in self.stop_words, tokens))
                text_content += f" {' '.join(tokens)}"

        # normalize, reshape for final word cloud
        text_content = self.normalizer.normalize(text_content)
        text_content = arabic_reshaper.reshape(text_content)
        text_content = get_display(text_content)
        logger.info('making wordcloud')
        #generate wordcloud
        wordcloud = WordCloud(
            width=width, height=height,
            font_path=str(DATA_DIR / 'BHoma.ttf'),
            background_color=background_color
        ).generate(text_content)
        logger.info(f'saving word cloud as png file!')
        wordcloud.to_file(str(Path(output_dir) / 'wordcloud.png'))


if __name__ == "__main__":
    chat_stats = ChatStatistics(chat_json=DATA_DIR / 'result.json')
    top_users = chat_stats.get_top_users(top_n=10)
    chat_stats.generate_word_cloud(output_dir=DATA_DIR)
    print(top_users)
print('done!')
