import json
from ctypes import Union
from pathlib import Path
from typing import Union

import arabic_reshaper
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
from hazm import *
from loguru import logger
from src.data import DATA_DIR
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
        stop_words = list(map(str.strip, stop_words))
        self.stop_words = list(map(self.normalizer.normalize, stop_words))

    def generate_word_cloud(self,
    output_dir: Union[str, Path],
    width: int = 800, height: int = 600,
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
            width=850, height=850,
            font_path=str(DATA_DIR / 'BHoma.ttf'),
            background_color='white'
        ).generate(text_content)
        logger.info(f'saving word cloud as png file!')
        wordcloud.to_file(str(Path(output_dir) / 'wordcloud.png'))


if __name__ == "__main__":
    chat_stats = ChatStatistics(chat_json=DATA_DIR / 'result.json')
    chat_stats.generate_word_cloud(output_dir=DATA_DIR)
print('done!')
