#Lerning Proc
import numpy as np
import caffe
from scipy import misc
from copy import copy
import random
import copy
import cv2
import os.path as osp
from os import listdir
from os.path import isfile, join

#Init network
caffe_root = '/media/anton/WorkAndStuff/CAFFE/caffenew0217/'
caffe.set_mode_gpu()
caffe.set_device(0)
workdir = '/media/anton/WorkAndStuff/OpenProject/BirdProject/SqNet'
solver = caffe.SGDSolver(osp.join(workdir, 'solver_supp.prototxt'))
solver.net.copy_from(osp.join(workdir, 'squeezenet_v1.1.caffemodel'))

#Load file afd foulders
def GetListWild(folder):
    List_Of_Adress = []
    onlyfiles = [f for f in listdir(folder) if isfile(join(folder, f))]
    for i in onlyfiles:
        filename, file_extension = osp.splitext(i)
        if(file_extension=='.jpg'):
            imgadress = osp.join(folder,i)
            textadress=osp.join(folder,filename+'.txt')
            List_Of_Adress.append([imgadress, textadress])
    return List_Of_Adress

BIRDBASE = GetListWild('/media/anton/Bazes/BIRD/FinalBase') # In list: jpg + txt adress

#Reshape to batch
random.seed(42)
batch_size=128
solver.net.blobs['data'].reshape(batch_size, 3,  227, 227)  # image size is 227x227
solver.net.blobs['label'].reshape(batch_size, 1 )  # image size is 227x227
solver.net.blobs['label_q'].reshape(batch_size, 1 )  # image size is 227x227
transformer = caffe.io.Transformer({'data': solver.net.blobs['data'].data.shape})

#Load to the memory for quick learning
def PrepareDataList(BASE, length):
    List = []
    for M in range(0,min(length,len(BASE))):
        img, text = BASE[M]
        image = misc.imread(img,mode='RGB')
        image = misc.imresize(image, [227, 227])
        r1 = []
        if isfile(text):
            f = open(text, 'r')
            s = f.readline()
            st = s.split(' ')
            for i in range(0,2):
                r1.append(int(st[i]))
            f.close()
        else: #If there are no txt file - "no bird situation"
            r1.append(0);
            r1.append(0);
        List.append([image,r1])
    return List

# Random test and train list
def SeparateList(L):
    Train=[]
    Test=[]
    fs = open('NumOfL', 'a')
    f2 = open('NumOfTest', 'a')
    j=0
    for Obj in L:
        M = random.randint(0,10)
        s, s2 = BIRDBASE[j]
        a, b = Obj
        if b[0] == 1:
            fs.write(s + ' ' + s2 + '\n')
        if (M<=9):
            Train.append(Obj)
        else:
            f2.write((s+' '+s2+' '+str(b[0])+'\n'))
            Test.append(Obj)
        j+=1
    fs.close()
    f2.close()
    return Train,Test

#Prepare data for learning
def PrepareDataFromList(i):
    mu = np.array([128.0, 128.0, 128.0])
    transformer.set_transpose('data', (2, 0, 1))
    transformer.set_mean('data', mu)
    transformed_image = transformer.preprocess('data', i)
    return transformed_image

#load in memory
ListData = PrepareDataList(BIRDBASE,2297)
ListData_train, ListData_test =SeparateList(ListData)

Age_Size = 1000
test_size=200
currit=0
for j in range(0,40):
    A = Age_Size
    if j<10:
      A=100
    solver.test_nets[0].share_with(solver.net)
    FullCorrect=0
    Semicorrect=0

####Test our recognition####
    for p in range(0, len(ListData_test)):
        i,r = copy.deepcopy(ListData_test[p])
        transformed_image = PrepareDataFromList(i)
        solver.test_nets[0].blobs['data'].data[0] = transformed_image
        solver.test_nets[0].forward()
        if (solver.test_nets[0].blobs['pool10'].data[0].argmax() == r[0]):
            FullCorrect+=1
    fs = open('ResultOfTest', 'a')
    fs.write(str(FullCorrect)  + ' '+str(currit) + ' '+ str(len(ListData_test))+'\n')
    fs.close()
############################
###Learn images for batch manualy
    for i in range(0, A):
        for in_batch in range(0, batch_size):
            R = random.randint(0, len(ListData_train) - 1)
            i, r = ListData_train[R]
            transformed_image = PrepareDataFromList(i)
            solver.net.blobs['data'].data[in_batch] = transformed_image
            solver.net.blobs['label'].data[in_batch] = r[0] #bird type
#Bird quality - differentt approach
            if (r[0]!=0):
                if (r[1] != 0):
                    solver.net.blobs['label_q'].data[in_batch] = 2
                else:
                    solver.net.blobs['label_q'].data[in_batch] = 1
            else:
                solver.net.blobs['label_q'].data[in_batch] =0
#Experiment with nolinear function
            '''''
            for k in range(0,9):
                solver.net.blobs['label_q'].data[in_batch][k]=0
            if (r[0] != 0):
                solver.net.blobs['label_q'].data[in_batch][r[1]] = 0.9
                if (r[1]-1>=0):
                    solver.net.blobs['label_q'].data[in_batch][r[1]-1] = 0.3
                if (r[1]+1<=8):
                    solver.net.blobs['label_q'].data[in_batch][r[1]+1] = 0.3
            '''

        solver.step(1)
    currit=currit+A