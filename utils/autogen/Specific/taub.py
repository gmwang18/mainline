# RunCrystal for Taub
import subprocess as sub
from submission_tools import LocalSubmitter
import os

# Where are your executibles stored?
BIN = "/home/busemey2/bin/"

if BIN[-1] != '/': BIN += '/'

#####################################################################
class LocalTaubSubmitter(LocalSubmitter):
  """Abstract submission class. Defines interaction with the queuing system."""
  # --------------------------------------------------------------
  def __init__(self,time='72:00:00',nn=1,np='allprocs', queue='batch'):
    """ Initialize a submitter object. 

    This part should contain all parts of calculation that user should care
    about, and all parts that are common to calculations of a certain type (all
    crystal SCF calculations, for instance)."""
    self.time  = time,
    self.nn    = nn
    self.np    = np
    self.queue = queue

  # --------------------------------------------------------------
  # Finds if any jobs in queue_ids are still in the queue.
  def _job_status(self,queue_ids):
    if type(queue_ids) != type([]):
      # Try to keep a standard data type for the queue_ids.
      # It's a list of strings, all ids must be done before continuing.
      print("Warning: queue_ids had to be cast to list!")
      print("Debug:",queue_ids)
      qids = [queue_ids]
    else: qids = queue_ids
    status = "finished"
    for qid in qids:
      try:
        qstat = sub.check_output(
            "qstat %s"%qid, stderr=sub.STDOUT, shell=True
          ).decode().split('\n')[-2].split()[4]
      except sub.CalledProcessError:
        # Non-bundled jobs might finish and be removed before others.
        qstat = "C"
      if qstat == "R" or qstat == "Q":
        return "running"
    if qstat == "C" or qstat == "E":
      status = "finished"
    return status

  # --------------------------------------------------------------
  def _job_cancel(self,queue_id):
    print("Cancel was called, but not implemented")

  # --------------------------------------------------------------
  def _qsub(self,exe,prep_commands=[],final_commands=[],
      name="",stdout="",loc=""):
    """ Helper function for executible submitters. 
    Should work in most cases to simplify code."""

    if stdout=="": stdout="stdout"
    if loc=="": loc=os.getcwd()
    if name=="": name=stdout
    header = []
    header.append("#!/bin/bash")
    if self.np=="allprocs": 
      header.append("#PBS -l nodes=%d,flags=allprocs"%self.nn)
    else:
      header.append("#PBS -l nodes=%d:ppn=%d"%(self.nn,self.np))
    header += [
      "#PBS -q %s"%self.queue,
      "#PBS -l walltime=%s"%self.time,
      "#PBS -j oe",
      "#PBS -m n",
      "#PBS -N %s"%name,
      "#PBS -o {0}".format(loc+"/qsub.out"),
      "module load openmpi/1.4-gcc+ifort"
    ]
    if self.np=="allprocs":
      exeline = "mpirun %s &> %s"%(exe, stdout)
    elif self.nn*self.np > 1:
      exeline = "mpirun -n %d %s &> %s"%(self.nn*self.np, exe, stdout)
    else:
      exeline = "%s &> %s"%(exe, stdout)
    commands = header + ["cd %s"%loc] + prep_commands + [exeline] + final_commands
    outstr = '\n'.join(commands)
    with open(loc+"/qsub.in",'w') as qsin:
      qsin.write(outstr)
    result = sub.check_output("qsub %s"%(loc+"/qsub.in"),shell=True)
    qid = result.decode().split()[0]
    print("Submitted as %s"%qid)
    return qid

#####################################################################
class LocalTaubCrystalSubmitter(LocalTaubSubmitter):
  """Fully defined submission class. Defines interaction with specific
  program to be run."""
  def _submit_job(self,inpfn,outfn="stdout",jobname="",loc=""):
    """ Submit a specific job to the queue. 
    
    Should not interact with user, and should receive only information specific
    to instance of a job run."""
    exe = BIN+"Pcrystal"
    prep_commands=["cp %s INPUT"%inpfn]
    final_commands = ["rm *.pe[0-9]","rm *.pe[0-9][0-9]"]

    if jobname == "":
      jobname = outfn
    if loc == "":
      loc = os.getcwd()

    qid = self._qsub(exe,prep_commands,final_commands,jobname,outfn,loc)
    return qid

#####################################################################
class LocalTaubPropertiesSubmitter(LocalTaubSubmitter):
  """Fully defined submission class. Defines interaction with specific
  program to be run."""
  def _submit_job(self,inpfn,outfn="stdout",jobname="",loc=""):
    """ Submit a specific job to the queue. 
    
    Should not interact with user, and should receive only information specific
    to instance of a job run."""
    exe = BIN+"properties < %s"%inpfn
    prep_commands = []
    final_commands = []

    if self.nn != 1 or self.np != 1:
      print("Refusing to run properties in parallel!")
      self.nn = 1
      self.np = 1

    if jobname == "":
      jobname = outfn
    if loc == "":
      loc = os.getcwd()

    qid = self._qsub(exe,prep_commands,final_commands,jobname,outfn,loc)
    return qid

#####################################################################
class LocalTaubQwalkSubmitter(LocalTaubSubmitter):
  """Fully defined submission class. Defines interaction with specific
  program to be run."""
  def _submit_job(self,inpfns,outfn="stdout",jobname="",loc=""):
    """ Submit a specific job to the queue. 
    
    Should not interact with user, and should receive only information specific
    to instance of a job run."""
    qids = []
    for inpfn in inpfns:
      exe = BIN+"qwalk %s"%inpfn
      prep_commands=[]
      final_commands=[]

      if jobname == "":
        jobname = outfn
      if loc == "":
        loc = os.getcwd()

      qids.append(self._qsub(exe,prep_commands,final_commands,jobname,outfn,loc))
    return qids

#####################################################################
class LocalTaubBundleQwalkSubmitter(LocalTaubSubmitter):
  """Fully defined submission class. Defines interaction with specific
  program to be run."""
  def _submit_job(self,inpfns,outfn="stdout",jobname="",loc=""):
    """ Submit a specific job to the queue. 
    
    Should not interact with user, and should receive only information specific
    to instance of a job run."""
    exe = " ".join([BIN+"bin/qwalk"]+inpfns)
    prep_commands=[]
    final_commands=[]

    if jobname == "":
      jobname = outfn
    if loc == "":
      loc = os.getcwd()

    qid = [self._qsub(exe,prep_commands,final_commands,jobname,outfn,loc)]
    return qid
