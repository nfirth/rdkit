# $Id$
#
#  Copyright (C) 2002-2008  greg Landrum and Rational Discovery LLC
#
#   @@ All Rights Reserved @@
#  This file is part of the RDKit.
#  The contents are covered by the terms of the BSD license
#  which is included in the file license.txt, found at the root
#  of the RDKit source tree.
#
"""unit testing code for the Crippen clogp and MR calculators

"""
from rdkit import RDConfig
import unittest,sys,os,cPickle
from rdkit import Chem
from rdkit.Chem import Crippen
import numpy

def feq(n1,n2,tol=1e-5):
  return abs(n1-n2)<=tol

class TestCase(unittest.TestCase):
  def setUp(self):
    self.fName = os.path.join(RDConfig.RDCodeDir,'Chem/test_data','Crippen.csv')
    self.detailName = os.path.join(RDConfig.RDCodeDir,'Chem/test_data','Crippen_contribs_regress.pkl')
    self.detailName2 = os.path.join(RDConfig.RDCodeDir,'Chem/test_data','Crippen_contribs_regress.2.pkl')

  def _readData(self):
    smis=[]
    clogs=[]
    mrs=[]
    for line in file(self.fName,'r').xreadlines():
      if len(line) and line[0] != '#':
        splitL = line.split(',')
        if len(splitL)==3:
          smi,clog,mr=splitL
          smis.append(smi)
          clogs.append(float(clog))
          mrs.append(float(mr))
    self.smis = smis
    self.clogs = clogs
    self.mrs = mrs
          
  def testLogP(self):
    self._readData()
    nMols = len(self.smis)
    #outF = file(self.fName,'w')
    for i in range(nMols):
      smi = self.smis[i]
      mol = Chem.MolFromSmiles(smi)

      if 1:
        clog = self.clogs[i]
        tmp = Crippen.MolLogP(mol)
        self.failUnless(feq(clog,tmp),'bad logp for %s: %4.4f != %4.4f'%(smi,clog,tmp))

        mr = self.mrs[i]
        tmp = Crippen.MolMR(mol)
        self.failUnless(feq(mr,tmp),'bad MR for %s: %4.4f != %4.4f'%(smi,mr,tmp))
      else:
        clog = Crippen.MolLogP(mol)
        mr = Crippen.MolMR(mol)
        print >>outF,'%s,%.4f,%.4f'%(smi,clog,mr)
  def testRepeat(self):
    self._readData()
    nMols = len(self.smis)
    for i in range(nMols):
      smi = self.smis[i]
      mol = Chem.MolFromSmiles(smi)

      clog = self.clogs[i]
      tmp = Crippen.MolLogP(mol)
      tmp = Crippen.MolLogP(mol)
      self.failUnless(feq(clog,tmp),'bad logp fooutF,r %s: %4.4f != %4.4f'%(smi,clog,tmp))

      mr = self.mrs[i]
      tmp = Crippen.MolMR(mol)
      tmp = Crippen.MolMR(mol)
      self.failUnless(feq(mr,tmp),'bad MR for %s: %4.4f != %4.4f'%(smi,mr,tmp))
      
  def _writeDetailFile(self,inF,outF):
    while 1:
      try:
        smi,refContribs = cPickle.load(inF)
      except EOFError:
        break
      else:
        try:
          mol = Chem.MolFromSmiles(smi)
        except:
          import traceback
          traceback.print_exc()
          mol = None
        if mol:
          mol=Chem.AddHs(mol,1)
          smi2 = Chem.MolToSmiles(mol)
          contribs = Crippen._GetAtomContribs(mol)
          cPickle.dump((smi,contribs),outF)
        else:
          print 'Problems with SMILES:',smi
  def _doDetailFile(self,inF,nFailsAllowed=1):
    done = 0
    verbose=0
    nFails=0
    while not done:
      if verbose: print '---------------'
      try:
        smi,refContribs = cPickle.load(inF)
      except EOFError:
        done = 1
      else:
        refContribs = [x[0] for x in refContribs]
        refOrder= numpy.argsort(refContribs)
        try:
          mol = Chem.MolFromSmiles(smi)
        except:
          import traceback
          traceback.print_exc()
          mol = None
        if mol:
          mol=Chem.AddHs(mol,1)
          smi2 = Chem.MolToSmiles(mol)
          contribs = Crippen._GetAtomContribs(mol)
          contribs = [x[0] for x in contribs]
          #
          #  we're comparing to the old results using the oelib code.
          #  Since we have some disagreements with them as to what is
          #  aromatic and what isn't, we may have different numbers of
          #  Hs. For the sake of comparison, just pop those off our
          #  new results.
          #
          while len(contribs)>len(refContribs):
            del contribs[-1]
          order = numpy.argsort(contribs)

          for i in range(len(refContribs)):
            refL = refContribs[refOrder[i]]
            l = contribs[order[i]]
            if not feq(refL,l):
              print '%s (%s): %d %6.5f != %6.5f'%(smi,smi2,order[i],refL,l)
              Crippen._GetAtomContribs(mol,force=1)
              print '-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*'
              nFails +=1
              break;
        else:
          print 'Problems with SMILES:',smi
    self.failUnless(nFails<nFailsAllowed)
  def testDetails(self):
    Crippen._Init()
    inF = open(self.detailName,'rb')
    if 0:
      outF = open('tmp.pkl','wb+')
      self._writeDetailFile(inF,outF)
    self._doDetailFile(inF)

  def testDetails2(self):
    Crippen._Init()
    inF = open(self.detailName2,'rb')
    if 0:
      outF = open('tmp.pkl','wb+')
      self._writeDetailFile(inF,outF)
    self._doDetailFile(inF)

  def testIssue80(self):
    from rdkit.Chem import Lipinski
    m = Chem.MolFromSmiles('CCOC')
    ref = Crippen.MolLogP(m)
    Lipinski.NHOHCount(m)
    probe = Crippen.MolLogP(m)
    self.failUnless(probe==ref)
    
  def testIssue1749494(self):
    m1 = Chem.MolFromSmiles('[*]CC')
    v = Crippen.MolLogP(m1)
    self.failUnless(feq(v,0.9739))
    
          
      
  
    
if __name__ == '__main__':
  unittest.main()

