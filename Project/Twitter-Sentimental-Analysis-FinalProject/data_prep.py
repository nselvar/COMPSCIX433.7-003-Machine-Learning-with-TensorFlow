from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
import numpy as np
import re
import random
import pandas as pd
import pickle
import os
from collections import Counter

lemm = WordNetLemmatizer()

def rand_list(lines, max_value):
    randlist = []
    for _ in range(lines):
        num = random.randint(0, max_value-1)
        while num in randlist:
            num = random.randint(0, max_value - 1)
        randlist.append(num)

    return randlist

def shuffler(input_ds, output_ds):
    df_source = pd.read_csv(input_ds, '<SP>', error_bad_lines=False,engine='python')
    df_shuffled = df_source.iloc[np.random.permutation(len(df_source))]
    # print(df_shuffled.head())
    df_shuffled.to_csv(output_ds, 'µ', index=False)


def smaller_dataset_gen(ds, newds, dsrows, num_lines=1000):
    count = 0
    with open(ds, 'r', 5000, 'latin-1') as raw_ds:
        with open(newds, 'w', 5000, encoding='utf8') as target_ds:
            selected_lines = rand_list(num_lines, dsrows)
            for line in raw_ds:
                if len(selected_lines) == 0:
                    break

                if count in selected_lines:
                    print(count)
                    target_ds.write(line)
                    selected_lines.remove(count)
                count += 1

    print("New dataset created with {} lines".format(num_lines))

def init_process(fin,fout):
    outfile = open(fout,'wb')
    count = 0
    with open(fin, buffering=200000, encoding="latin-1") as f:
        try:
            for line in f:
                count +=1
                if len(line) == 0:
                    break
                if count == 100000:
                    break
                print(count)
                outfile.write(line.encode("latin-1"))
        except Exception as e:
            print(str(e))
        outfile.close()



def clean_dataset(ds, ods):
    with open(ds, 'r', 30000, 'latin-1') as raw_ds:
        with open('tempds.csv', 'w', 20000,'latin-1') as cleaned_ds:
            for line in raw_ds:
                result = re.search('^"(\d)",.*,"(.*)"$', line)
                new_line = result.group(1) + '<SP>' + result.group(2) + '\n'
                cleaned_ds.write(new_line)

        shuffler('tempds.csv', ods)
        os.remove('tempds.csv')
    print("Dataset cleanup done")


# Responsible to create a list with all the words that matter already lemmatized
def create_word_dict(source_ds):
    word_dict = []
    with open(source_ds, 'r', buffering=200000, encoding='latin-1') as ds:
        count=0
        for line in ds:
            count+=1
            print(count)
            text = line.split('µ')[1]
            words = word_tokenize(text.lower())
            lemm_words = [lemm.lemmatize(w) for w in words]
            word_dict += list(lemm_words)

        word_count = Counter(word_dict)

    cleaned_word_dict = [word for word in word_count if 1000 > word_count[word] > 60]
    dict_size = len(cleaned_word_dict)

    print("Word dictionary size: {}".format(dict_size))
    with open('process/word_dict.pickle', 'wb') as wd:
        pickle.dump(cleaned_word_dict, wd)

    print("Word dictionary generated and saved")
    return dict_size


# Prepares the sentences changing them into the hot vector
def sentence_to_vector(word_dict_file, cleaned_ds, output_file):

    with open(cleaned_ds, 'r', 30000, 'latin-1') as ds:
        with open(word_dict_file, 'rb') as wd:
            word_dict = pickle.load(wd)
            num_lines = 0
            # print(len(word_dict))
            # print(word_dict)
            with open(output_file, 'wb') as hv:
                count=0
                for line in ds:
                    count+=1
                    print(count)
                    hot_vector = np.zeros(len(word_dict))
                    if line.count('µ') == 1:
                        sentiment, text = line.split('µ')
                        words = word_tokenize(text.lower())
                        lemm_words = [lemm.lemmatize(w) for w in words]
                        for word in lemm_words:
                            if word in word_dict:
                                hot_vector[word_dict.index(word)] += 1
                        hot_vector = list(hot_vector)

                        clean_sentiment = re.search('.*(\d).*', sentiment)

                        if int(clean_sentiment.group(1)) == 0:
                            sentiment = [1, 0]
                        else:
                            sentiment = [0, 1]

                        # print(hot_vector, sentiment)
                        num_lines += 1

                        pickle.dump([hot_vector, sentiment], hv)

                print('Hot vectors file generated with {} lines'.format(num_lines))
    return num_lines

# init_process('test/training.1600000.processed.noemoticon.csv','process/smaller_ds.csv')

def cleanAndLoad():

    smaller_dataset_gen('test/training.1600000.processed.noemoticon.csv', 'process/smaller_ds.csv', 1600000, 50000)
    clean_dataset('test/training.1600000.processed.noemoticon.csv', 'process/result.csv')
    clean_dataset('process/smaller_ds.csv', 'process/small_train.csv')
    clean_dataset('test/testdata.manual.2009.06.14.csv', 'process/test.csv')

    with open('process/data_details.pkl', 'wb') as details:
        dict_size = create_word_dict('process/small_train.csv')
        train_size = sentence_to_vector('process/word_dict.pickle', 'process/small_train.csv', 'process/train_hot_vectors.pickle')
        test_size = sentence_to_vector('process/word_dict.pickle', 'process/test.csv', 'process/test_hot_vectors.pickle')
        details_sizes = {'dict': dict_size, 'train': train_size, 'test': test_size}
        pickle.dump(details_sizes, details)

cleanAndLoad()