# -*- coding: utf-8 -*-
"""MemNet_ABSA.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1rUSRvxE7QlihOwsfXfMZs-dUTHHHtlGE
"""

!git clone https://github.com/Humanity123/MemNet_ABSA.git

# %cd MemNet_ABSA/

#!rm main.py

"""%%writefile main.py
import os
import pprint
import tensorflow as tf

from nltk import word_tokenize
from data import *
from model import MemN2N

pp = pprint.PrettyPrinter()

flags = tf.app.flags

flags.DEFINE_integer("edim", 300, "internal state dimension [300]")
flags.DEFINE_integer("lindim", 300, "linear part of the state [75]")
flags.DEFINE_integer("nhop", 3, "number of hops [7]")
flags.DEFINE_integer("batch_size", 1, "batch size to use during training [128]")
flags.DEFINE_integer("nepoch", 10, "number of epoch to use during training [100]")
flags.DEFINE_float("init_lr", 0.01, "initial learning rate [0.01]")
flags.DEFINE_float("init_hid", 0.1, "initial internal state value [0.1]")
flags.DEFINE_float("init_std", 0.01, "weight initialization std [0.05]")
flags.DEFINE_float("max_grad_norm", 100, "clip gradients to this norm [50]")
flags.DEFINE_string("pretrain_file", "../gdrive/My Drive/Infersent/dataset/GloVe/glove.840B.300d.txt", "pre-trained glove vectors file path [../gdrive/My Drive/Infersent/dataset/GloVe/glove.840B.300d.txt]")
flags.DEFINE_string("train_data", "data/Laptops_Train.xml.seg", "train gold data set path [./data/Laptops_Train.xml.seg]")
flags.DEFINE_string("test_data", "data/Laptops_Test_Gold.xml.seg", "test gold data set path [./data/Laptops_Test_Gold.xml.seg]")
flags.DEFINE_boolean("show", False, "print progress [False]")

FLAGS = flags.FLAGS

def main(_):
  source_count, target_count = [], []
  source_word2idx, target_word2idx, word_set = {}, {}, {}
  max_sent_len = -1
  
  max_sent_len = get_dataset_resources(FLAGS.train_data, source_word2idx, target_word2idx, word_set, max_sent_len)
  max_sent_len = get_dataset_resources(FLAGS.test_data, source_word2idx, target_word2idx, word_set, max_sent_len)
  embeddings = load_embedding_file(FLAGS.pretrain_file, word_set)

  train_data = get_dataset(FLAGS.train_data, source_word2idx, target_word2idx, embeddings)
  test_data = get_dataset(FLAGS.test_data, source_word2idx, target_word2idx, embeddings)

  print("train data size - ", len(train_data[0]))
  print ("test data size - ", len(test_data[0]))

  print ("max sentence length - ",max_sent_len)
  FLAGS.pad_idx = source_word2idx['<pad>']
  FLAGS.nwords = len(source_word2idx)
  FLAGS.mem_size = max_sent_len

  pp.pprint(flags.FLAGS.__flags)

  print('loading pre-trained word vectors...')
  print('loading pre-trained word vectors for train and test data')
  
  FLAGS.pre_trained_context_wt, FLAGS.pre_trained_target_wt = get_embedding_matrix(embeddings, source_word2idx,  target_word2idx, FLAGS.edim)
  
  with tf.Session() as sess:
    model = MemN2N(FLAGS, sess)
    model.build_model()
    model.run(train_data, test_data)  

if __name__ == '__main__':
  tf.app.run()
"""

#!rm data.py

"""%%writefile data.py
from nltk import word_tokenize
from collections import Counter
from nltk.corpus import stopwords

import numpy as np
import os
import xml.etree.ElementTree as ET
import html
import html.parser
import re

stop = set(stopwords.words('english')) 

def load_embedding_file(embed_file_name, word_set):
  ''' loads embedding file and returns a dictionary (word -> embedding) for the words existing in the word_set '''

  embeddings = {}
  with open(embed_file_name, 'r') as embed_file:
    for line in embed_file:
      content = line.strip().split()
      word = ''.join(content[:-300])
      if word in word_set:
        embedding = np.asarray(content[-300:] , dtype='float32')
        embeddings[word] = embedding

  return embeddings

def get_dataset_resources(data_file_name, sent_word2idx, target_word2idx, word_set, max_sent_len):
  ''' updates word2idx and word_set '''
  if len(sent_word2idx) == 0:
    sent_word2idx["<pad>"] = 0

  word_count = []
  sent_word_count = []
  target_count = []

  words = []
  sentence_words = []
  target_words = []

  with open(data_file_name, 'r') as data_file:
    lines = data_file.read().split('\n')
    for line_no in range(0, len(lines)-1, 3):
      sentence = lines[line_no]
      target = lines[line_no+1]

      sentence.replace("$T$", "")
      sentence = sentence.lower()
      target = target.lower()
      max_sent_len = max(max_sent_len, len(sentence.split()))
      sentence_words.extend(sentence.split())
      target_words.extend([target])
      words.extend(sentence.split() + target.split())

    sent_word_count.extend(Counter(sentence_words).most_common())
    target_count.extend(Counter(target_words).most_common())
    word_count.extend(Counter(words).most_common())

    for word, _ in sent_word_count:
      if word not in sent_word2idx:
        sent_word2idx[word] = len(sent_word2idx)

    for target, _ in target_count:
      if target not in target_word2idx:
        target_word2idx[target] = len(target_word2idx)    

    for word, _ in word_count:
      if word not in word_set:
        word_set[word] = 1

  return max_sent_len

def get_embedding_matrix(embeddings, sent_word2idx,  target_word2idx, edim):
  ''' returns the word and target embedding matrix ''' 
  word_embed_matrix = np.zeros([len(sent_word2idx), edim], dtype = float)
  target_embed_matrix = np.zeros([len(target_word2idx), edim], dtype = float)

  for word in sent_word2idx:
    if word in embeddings:
      word_embed_matrix[sent_word2idx[word]] = embeddings[word]

  for target in target_word2idx:
    for word in target:
      if word in embeddings:
        target_embed_matrix[target_word2idx[target]] += embeddings[word]
    target_embed_matrix[target_word2idx[target]] /= max(1, len(target.split()))

  print (type(word_embed_matrix))
  return word_embed_matrix, target_embed_matrix


def get_dataset(data_file_name, sent_word2idx, target_word2idx, embeddings):
  ''' returns the dataset'''
  sentence_list = []
  location_list = []
  target_list = []
  polarity_list = []


  with open(data_file_name, 'r') as data_file:
    lines = data_file.read().split('\n')
    for line_no in range(0, len(lines)-1, 3):
      sentence = lines[line_no].lower()
      target = lines[line_no+1].lower()
      polarity = int(lines[line_no+2])

      sent_words = sentence.split()
      target_words = target.split()
      try:
        target_location = sent_words.index("$t$")
      except:
        print ("sentence does not contain target element tag")
        exit()

      is_included_flag = 1
      id_tokenised_sentence = []
      location_tokenised_sentence = []
      
      for index, word in enumerate(sent_words):
        if word == "$t$":
          continue
        try:
          word_index = sent_word2idx[word]
        except:
          print ("id not found for word in the sentence")
          exit()

        location_info = abs(index - target_location)

        if word in embeddings:
          id_tokenised_sentence.append(word_index)
          location_tokenised_sentence.append(location_info)

        # if word not in embeddings:
        #   is_included_flag = 0
        #   break

      is_included_flag = 0
      for word in target_words:
        if word in embeddings:
          is_included_flag = 1
          break
          

      try:
        target_index = target_word2idx[target]
      except:
        print (target)
        print ("id not found for target")
        exit()


      if not is_included_flag:
        print(sentence)
        continue

      sentence_list.append(id_tokenised_sentence)
      location_list.append(location_tokenised_sentence)
      target_list.append(target_index)
      polarity_list.append(polarity)

  return sentence_list, location_list, target_list, polarity_list
"""

import nltk
nltk.download('stopwords')

#!rm model.py

"""%%writefile model.py
import os
import sys
import math
import random
import numpy as np
import tensorflow as tf
from past.builtins import xrange
import time as tim

class MemN2N(object):
    def __init__(self, config, sess):
        self.nwords = config.nwords
        self.init_hid = config.init_hid
        self.init_std = config.init_std
        self.batch_size = config.batch_size
        self.nepoch = config.nepoch
        self.nhop = config.nhop
        self.edim = config.edim
        self.mem_size = config.mem_size
        self.lindim = config.lindim
        self.max_grad_norm = config.max_grad_norm
        self.pad_idx = config.pad_idx
        self.pre_trained_context_wt = config.pre_trained_context_wt
        self.pre_trained_target_wt = config.pre_trained_target_wt

        self.input = tf.placeholder(tf.int32, [self.batch_size, 1], name="input")
        self.time = tf.placeholder(tf.int32, [None, self.mem_size], name="time")
        self.target = tf.placeholder(tf.int64, [self.batch_size], name="target")
        self.context = tf.placeholder(tf.int32, [self.batch_size, self.mem_size], name="context")
        self.mask = tf.placeholder(tf.float32, [self.batch_size, self.mem_size], name="mask")
        self.neg_inf = tf.fill([self.batch_size, self.mem_size], -1*np.inf, name="neg_inf")

        self.show = config.show

        self.hid = []

        self.lr = None
        self.current_lr = config.init_lr
        self.loss = None
        self.step = None
        self.optim = None

        self.sess = sess
        self.log_loss = []
        self.log_perp = []

    def build_memory(self):
      self.global_step = tf.Variable(0, name="global_step")

      self.A = tf.Variable(tf.random_uniform([self.nwords, self.edim], minval=-0.01, maxval=0.01))
      self.ASP = tf.Variable(tf.random_uniform([self.pre_trained_target_wt.shape[0], self.edim], minval=-0.01, maxval=0.01))
      self.C = tf.Variable(tf.random_uniform([self.edim, self.edim], minval=-0.01, maxval=0.01))
      self.C_B =tf.Variable(tf.random_uniform([1, self.edim], minval=-0.01, maxval=0.01))
      self.BL_W = tf.Variable(tf.random_uniform([2 * self.edim, 1], minval=-0.01, maxval=0.01))
      self.BL_B = tf.Variable(tf.random_uniform([1, 1], minval=-0.01, maxval=0.01))

      self.Ain_c = tf.nn.embedding_lookup(self.A, self.context)
      self.Ain = self.Ain_c

      self.ASPin = tf.nn.embedding_lookup(self.ASP, self.input)
      self.ASPout2dim = tf.reshape(self.ASPin, [-1, self.edim])
      self.hid.append(self.ASPout2dim)

      for h in xrange(self.nhop):
        '''
        Bi-linear scoring function for a context word and aspect term
        '''
        self.til_hid = tf.tile(self.hid[-1], [1, self.mem_size])
        self.til_hid3dim = tf.reshape(self.til_hid, [-1, self.mem_size, self.edim])
        self.a_til_concat = tf.concat(axis=2, values=[self.til_hid3dim, self.Ain])
        self.til_bl_wt = tf.tile(self.BL_W, [self.batch_size, 1])
        self.til_bl_3dim = tf.reshape(self.til_bl_wt, [self.batch_size,  2 * self.edim, -1])
        self.att = tf.matmul(self.a_til_concat, self.til_bl_3dim)
        self.til_bl_b = tf.tile(self.BL_B, [self.batch_size, self.mem_size])
        self.til_bl_3dim = tf.reshape(self.til_bl_b, [-1, self.mem_size, 1])
        self.g = tf.nn.tanh(tf.add(self.att, self.til_bl_3dim))
        self.g_2dim = tf.reshape(self.g, [-1, self.mem_size])
        self.masked_g_2dim = tf.add(self.g_2dim, self.mask)
        self.P = tf.nn.softmax(self.masked_g_2dim)
        self.probs3dim = tf.reshape(self.P, [-1, 1, self.mem_size])


        self.Aout = tf.matmul(self.probs3dim, self.Ain)
        self.Aout2dim = tf.reshape(self.Aout, [self.batch_size, self.edim])

        Cout = tf.matmul(self.hid[-1], self.C)
        til_C_B = tf.tile(self.C_B, [self.batch_size, 1])
        Cout_add = tf.add(Cout, til_C_B)
        self.Dout = tf.add(Cout_add, self.Aout2dim)

        if self.lindim == self.edim:
            self.hid.append(self.Dout)
        elif self.lindim == 0:
            self.hid.append(tf.nn.relu(self.Dout))
        else:
            F = tf.slice(self.Dout, [0, 0], [self.batch_size, self.lindim])
            G = tf.slice(self.Dout, [0, self.lindim], [self.batch_size, self.edim-self.lindim])
            K = tf.nn.relu(G)
            self.hid.append(tf.concat(axis=1, values=[F, K]))

    def build_model(self):
      self.build_memory()

      self.W = tf.Variable(tf.random_uniform([self.edim, 3], minval=-0.01, maxval=0.01))
      self.z = tf.matmul(self.hid[-1], self.W)
      
      self.loss = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=self.z, labels=self.target)

      self.lr = tf.Variable(self.current_lr)
      self.opt = tf.train.AdagradOptimizer(self.lr)

      params = [self.A, self.C, self.C_B, self.W, self.BL_W, self.BL_B]

      self.loss = tf.reduce_sum(self.loss) 

      grads_and_vars = self.opt.compute_gradients(self.loss,params)
      clipped_grads_and_vars = [(tf.clip_by_norm(gv[0], self.max_grad_norm), gv[1]) \
                                for gv in grads_and_vars]

      inc = self.global_step.assign_add(1)
      with tf.control_dependencies([inc]):
          self.optim = self.opt.apply_gradients(clipped_grads_and_vars)

      tf.initialize_all_variables().run()

      self.correct_prediction = tf.argmax(self.z, 1)

    def train(self, data):
      source_data, source_loc_data, target_data, target_label= data
      N = int(math.ceil(len(source_data) / self.batch_size))
      cost = 0

      x = np.ndarray([self.batch_size, 1], dtype=np.int32)
      time = np.ndarray([self.batch_size, self.mem_size], dtype=np.int32)
      target = np.zeros([self.batch_size], dtype=np.int32) 
      context = np.ndarray([self.batch_size, self.mem_size], dtype=np.int32)
      mask = np.ndarray([self.batch_size, self.mem_size])
      
      if self.show:
        from utils import ProgressBar
        bar = ProgressBar('Train', max=N)

      rand_idx, cur = np.random.permutation(len(source_data)), 0
      for idx in xrange(N):
        if self.show: bar.next()
        
        context.fill(self.pad_idx)
        time.fill(self.mem_size)
        target.fill(0)
        mask.fill(-1.0*np.inf)
        

        for b in xrange(self.batch_size):
            m = rand_idx[cur]
            x[b][0] = target_data[m]
            target[b] = target_label[m]
            time[b,:len(source_loc_data[m])] = source_loc_data[m]
            context[b,:len(source_data[m])] = source_data[m]
            mask[b,:len(source_data[m])].fill(0)
            cur = cur + 1
 
        z, a, loss, self.step = self.sess.run([ self.z, self.optim,
                                            self.loss,
                                            self.global_step],
                                            feed_dict={
                                                self.input: x,
                                                self.time: time,
                                                self.target: target,
                                                self.context: context,
                                                self.mask: mask})
        
        
       
        if idx%500 == 0:
            print ("loss - ", loss)

        cost += np.sum(loss)
      
      if self.show: bar.finish()
      _, train_acc = self.test(data)
      return cost/N/self.batch_size, train_acc

    def test(self, data):
      source_data, source_loc_data, target_data, target_label = data
      N = int(math.ceil(len(source_data) / self.batch_size))
      cost = 0

      x = np.ndarray([self.batch_size, 1], dtype=np.int32)
      time = np.ndarray([self.batch_size, self.mem_size], dtype=np.int32)
      target = np.zeros([self.batch_size], dtype=np.int32) 
      context = np.ndarray([self.batch_size, self.mem_size], dtype=np.int32)
      mask = np.ndarray([self.batch_size, self.mem_size])

      context.fill(self.pad_idx)

      m, acc = 0, 0
      for i in xrange(N):
        target.fill(0)
        time.fill(self.mem_size)
        context.fill(self.pad_idx)
        mask.fill(-1.0*np.inf)
        
        raw_labels = []
        for b in xrange(self.batch_size):
          x[b][0] = target_data[m]
          target[b] = target_label[m]
          time[b,:len(source_loc_data[m])] = source_loc_data[m]
          context[b,:len(source_data[m])] = source_data[m]
          mask[b,:len(source_data[m])].fill(0)
          raw_labels.append(target_label[m])
          m += 1

        loss = self.sess.run([self.loss],
                                        feed_dict={
                                            self.input: x,
                                            self.time: time,
                                            self.target: target,
                                            self.context: context,
                                            self.mask: mask})
        cost += np.sum(loss)

        predictions = self.sess.run(self.correct_prediction, feed_dict={self.input: x,
                                                     self.time: time,
                                                     self.target: target,
                                                     self.context: context,
                                                     self.mask: mask})

        for b in xrange(self.batch_size):
          if raw_labels[b] == predictions[b]:
            acc = acc + 1

      return cost, acc/float(len(source_data))

    def run(self, train_data, test_data):
      print('training...')
      self.sess.run(self.A.assign(self.pre_trained_context_wt))
      self.sess.run(self.ASP.assign(self.pre_trained_target_wt))

      for idx in xrange(self.nepoch):
        print('epoch '+str(idx)+'...')
        train_loss, train_acc = self.train(train_data)
        test_loss, test_acc = self.test(test_data)
        print('train-loss=%.2f;train-acc=%.2f;test-acc=%.2f;' % (train_loss, train_acc, test_acc))
        self.log_loss.append([train_loss, test_loss])
"""

!pip install tensorflow==1.4.1

pip install --upgrade --force-reinstall progress

from google.colab import drive
drive.mount('/content/gdrive')

!python main.py --show True

