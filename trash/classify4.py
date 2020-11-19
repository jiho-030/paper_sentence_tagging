#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#-*-coding:utf-8-sig-*- 
import sys
import argparse
import pandas as pd
import torch
import torch.nn as nn
from torchtext import data
from collections import Counter

from simple_ntc.models.rnn import RNNClassifier
from simple_ntc.models.cnn import CNNClassifier


def define_argparser():
    '''
    Define argument parser to take inference using pre-trained model.
    '''
    p = argparse.ArgumentParser()

    p.add_argument('--model_fn', required=True)
    #p.add_argument('--test_fn', required=True)
    p.add_argument('--gpu_id', type=int, default=-1)
    p.add_argument('--batch_size', type=int, default=256)
    p.add_argument('--top_k', type=int, default=2)
    p.add_argument('--max_length', type=int, default=256)
    
    p.add_argument('--drop_rnn', action='store_true')
    p.add_argument('--drop_cnn', action='store_true')

    config = p.parse_args()

    return config

def read_text(max_length=256):
    text = pd.read_csv("./simple_ntc/data/test_token.tsv", delimiter='\t', names=['tag', 'sentence'])
    text2 = text['sentence']

    lines =[]

    for line in text2:
        if line.strip() != '':
            lines += [line.strip().split(' ')][:max_length]

    label = text['tag']

    return lines, label

def define_field():
    '''
    To avoid use DataLoader class, just declare dummy fields. 
    With those fields, we can retore mapping table between words and indice.
    '''
    return (
        data.Field(
            use_vocab=True,
            batch_first=True,
            include_lengths=False,
        ),
        data.Field(
            sequential=False,
            use_vocab=True,
            unk_token=None,
        )
    )


def main(config):
    
    saved_data = torch.load(
        config.model_fn,
        map_location='cpu' if config.gpu_id < 0 else 'cuda:%d' % config.gpu_id
    )

    train_config = saved_data['config']
    rnn_best = saved_data['rnn']
    cnn_best = saved_data['cnn']
    vocab = saved_data['vocab']
    classes = saved_data['classes']

    vocab_size = len(vocab)
    n_classes = len(classes)

    text_field, label_field = define_field()
    text_field.vocab = vocab
    label_field.vocab = classes

    lines, label = read_text(max_length=config.max_length)

    with torch.no_grad():
        ensemble = []
        if rnn_best is not None and not config.drop_rnn:
            # Declare model and load pre-trained weights.
            model = RNNClassifier(
                input_size=vocab_size,
                word_vec_size=train_config.word_vec_size,
                hidden_size=train_config.hidden_size,
                n_classes=n_classes,
                n_layers=train_config.n_layers,
                dropout_p=train_config.dropout,
            )
            model.load_state_dict(rnn_best)
            ensemble += [model]
        if cnn_best is not None and not config.drop_cnn:
            # Declare model and load pre-trained weights.
            model = CNNClassifier(
                input_size=vocab_size,
                word_vec_size=train_config.word_vec_size,
                n_classes=n_classes,
                use_batch_norm=train_config.use_batch_norm,
                dropout_p=train_config.dropout,
                window_sizes=train_config.window_sizes,
                n_filters=train_config.n_filters,
            )
            model.load_state_dict(cnn_best)
            ensemble += [model]

        y_hats = []
        # Get prediction with iteration on ensemble.
        for model in ensemble:
            if config.gpu_id >= 0:
                model.cuda(config.gpu_id)
            # Don't forget turn-on evaluation mode.
            model.eval()

            y_hat = []
            for idx in range(0, len(lines), config.batch_size):                
                # Converts string to list of index.
                x = text_field.numericalize(
                    text_field.pad(lines[idx:idx + config.batch_size]),
                    device='cuda:%d' % config.gpu_id if config.gpu_id >= 0 else 'cpu',
                )

                y_hat += [model(x).cpu()]
            # Concatenate the mini-batch wise result
            y_hat = torch.cat(y_hat, dim=0)
            # |y_hat| = (len(lines), n_classes)

            y_hats += [y_hat]

            model.cpu()
        # Merge to one tensor for ensemble result and make probability from log-prob.
        y_hats = torch.stack(y_hats).exp()
        # |y_hats| = (len(ensemble), len(lines), n_classes)
        y_hats = y_hats.sum(dim=0) / len(ensemble) # Get average
        # |y_hats| = (len(lines), n_classes)

        probs, indice = y_hats.topk(config.top_k)
        '''
        for i in range(30):
            
            sys.stdout.write('%s\t%s\n' % (
                ' '.join([classes.itos[indice[i][j]] for j in range(config.top_k)]), 
                ' '.join(lines[i])
                ))
        '''    
            #print([indice[i][j] for j in range(config.top_k)], [classes.itos[indice[i][j]] for j in range(config.top_k)], label[i])
        '''    
        correct = 0
        total = 0
        for i in range(len(lines)):
            if [label[i]] == [classes.itos[indice[i][j]] for j in range(config.top_k)]:
                correct += 1
        print('Accuracy: %d %%' % (100 * correct / len(lines)))        
        '''
        

        count1 = 0
        count2 = 0
        count3 = 0
        count4 = 0
        cnt = Counter()
        for i in range(len(lines)):
            if [label[i]] == [classes.itos[indice[i][0]]] or [classes.itos[indice[i][1]]] :
                if abs(probs[i][0] - probs[i][1]) <= 0.1 :
                    twoclasses = [ classes.itos[indice[i][0]] , classes.itos[indice[i][1]] ]
                    diff = float(abs(probs[i][0] - probs[i][1]))
                    for two in twoclasses :
                        cnt[two] += 1
        print(cnt)                
                    two classes = [ [가설 설정, 이론모형] , [가설 설정, 데이터처리] ,
                    
                    
'''
                    for t in twoclasses :
                        if t == [ '가설 설정', '이론/모형' ] :
                            count1 += 1
                        if t == [ '가설 설정', '데이터처리'] :
                            count2 += 1
                        if t == [ '가설 설정', '대상 데이터' ] :
                            count3 += 1
                        if t == [ '가설 설정', '제안 방법'] :
                            count4 += 1
                        
        print('가설 설정, 이론/모형 : ', count1)
        print('가설 설정, 데이터처리 : ', count2)
        print('가설 설정, 대상 데이터 : ', count3)
        print('가설 설정, 제안 방법 : ', count4)
'''                        
                            
                            

if __name__ == '__main__':
    config = define_argparser()
    main(config)