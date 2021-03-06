#!/usr/bin/env python

"""
This script can do three things:
  (1) generate validation reference(s) for given benchmark(s)
  (2) compare benchmark(s) to their reference(s)
  (3) show visually differences between benchmark(s) and their reference(s)

Usage
#######
python validation.py [-c] [-h] [-v] [-b <bench_case> [-o <nb_OMPThreads>] [-m <nb_MPIProcs>] [-g | -s]]

For help on options, try 'python validation.py -h'


Here are listed the files used in the validation process:
#########################################################
The "validation" directory which contains:
  - the "references" directory with one file for each benchmark
  - validation files (prefixed with "validate_") for each benchmark
  - a "workdirs" directory, created during the validation process
  - archived "workdirs" for previous versions of smilei

A "workdirs" contains:
 - the smilei binary : "smilei"
 - the compilation output : "compilation_output"
 - a directory wd_<input_file>/<o>/<m> directory, containing the output files
 or
 - the compilation errors file : "compilation_errors"

The different steps of the script are the folllowing :
######################################################
Compilation step :
+++++++++++++++
If the "workdirs" directory lacks a smilei binary, or it is too old),
then the "workdirs" is backed up, and a new compilation occurs.
If compiling errors occur, "compilation_errors" is created and the script exits with status 3.

Execution step :
+++++++++++++++
If wd_<input_file>/<o>/<m> does not exist then:
- it is created
- smilei is executed in that directory for the requested benchmark
- if execution fails, the script exits with status 2

Validation step :
+++++++++++++++
Loops through all requested benchmarks
	Runs the benchmark in the workdir
	If requested to generate references:
		Executes the "validate_*" script and stores the result as reference data
	If requested to compare to previous references
		Executes the "validate_*" script and compares the result to the reference data
	If requested to show differences to previous references
		Executes the "validate_*" script and plots the result vs. the reference data

Exit status of the script
+++++++++++++++++++++++++
0  validated
1  validation fails
2  execution fails
3  compilation fails
4  bad option

Remark
+++++++
This script may run anywhere: you can define a SMILEI_ROOT environment variable
"""


# IMPORTS
import sys, os, re, glob, time
import shutil, getopt, inspect, socket, pickle
from subprocess import check_call,CalledProcessError,call
s = os.sep

# SMILEI PATH VARIABLES
if "SMILEI_ROOT" in os.environ :
	SMILEI_ROOT=os.environ["SMILEI_ROOT"]+s
else :
	SMILEI_ROOT = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))+s+".."+s
	#SMILEI_ROOT = os.getcwd()+s+".."+s
SMILEI_ROOT = os.path.abspath(SMILEI_ROOT)+s
SMILEI_SCRIPTS = SMILEI_ROOT+"scripts"+s
SMILEI_VALIDATION = SMILEI_ROOT+"validation"+s
SMILEI_REFERENCES = SMILEI_VALIDATION+"references"+s
SMILEI_BENCHS = SMILEI_ROOT+"benchmarks"+s

# SCRIPTS VARIABLES
EXEC_SCRIPT = 'exec_script.sh'
EXEC_SCRIPT_OUT = 'exec_script.out'
SMILEI_EXE_OUT = 'smilei_exe.out'

# Load the Smilei module
execfile(SMILEI_SCRIPTS+"Diagnostics.py")

# OTHER VARIABLES
POINCARE = "poincare"
JOLLYJUMPER = "llrlsi-gw"
HOSTNAME = socket.gethostname()

# DEFAULT VALUES FOR OPTIONS
OMP = 4
MPI = 4
EXECUTION = False
VERBOSE = False
BENCH=""
COMPILE_ONLY = False
GENERATE = False
SHOWDIFF = False

# TO PRINT USAGE
def usage():
	print 'Usage: validation.py [-c] [-h] [-v] [-b <bench_case> [-o <nb_OMPThreads>] [-m <nb_MPIProcs>] [-g | -s]]'

# GET COMMAND-LINE OPTIONS
try:
	options, remainder = getopt.getopt(
		sys.argv[1:],
		'o:m:b:gshvc',
		['OMP=', 'MPI=', 'BENCH=', 'COMPILE_ONLY=', 'GENERATE=', 'HELP=', 'VERBOSE='])
except getopt.GetoptError as err:
	usage()
	sys.exit(4)

# PROCESS THE OPTIONS
for opt, arg in options:
	if opt in ('-o', '--OMP'):
		EXECUTION = True
		OMP = int(arg)
	elif opt in ('-m', '--MPI'):
		EXECUTION = True
		MPI = int(arg)
	elif opt in ('-b', '--BENCH'):
		BENCH = arg
	elif opt in ('-c', '--COMPILEONLY'):
		COMPILE_ONLY=True
	elif opt in ('-h', '--HELP'):
		print "-b"
		print "     -b <bench_case>"
		print "       <bench_case> : benchmark(s) to validate. Accepts wildcards."
		print "       <bench_case>=? : ask input for a benchmark"
		print "     DEFAULT : All benchmarks are validated."  
		print "-o"
		print "     -o <nb_OMPThreads>"
		print "       <nb_OMPThreads> : number of OpenMP threads used for the execution"
		print "     DEFAULT : 4"  
		print "-m"
		print "     -m <nb_MPIProcs>"
		print "       <nb_MPIProcs> : number of MPI processes used for the execution"
		print "     DEFAULT : 4"
		print "-g"
		print "     Generation of references only"
		print "-s"
		print "     Plot differences with references only"
		print "-c"
		print "     Compilation only"
		print "-v"
		print "     Verbose"
		exit()
	elif opt in ('-g', '--GENERATE'):
		GENERATE = True
	elif opt in ('-s', '--SHOW'):
		SHOWDIFF = True
	elif opt in ('-v', '--VERBOSE'):
		VERBOSE = True

if GENERATE and SHOWDIFF:
	usage()
	sys.exit(4)

# Build the list of the requested input files
list_bench = [os.path.basename(b) for b in glob.glob(SMILEI_BENCHS+"tst*py")]
list_validation = [os.path.basename(b) for b in glob.glob(SMILEI_VALIDATION+"validate_tst*py")]
list_bench = [b for b in list_bench if "validate_"+b in list_validation]
if BENCH == "":
	SMILEI_BENCH_LIST = list_bench
elif BENCH == "?":
	VERBOSE = True
	os.chdir(SMILEI_SCRIPTS)
	#- Propose the list of all the input files
	print '\n'.join(list_bench)
	#- Choose an input file name in the list
	print 'Enter an input file from the list above:'
	BENCH = raw_input()
	SMILEI_BENCH_LIST = [ BENCH ]
	while BENCH not in list_bench:
		print "Input file "+BENCH+" invalid. Try again."
		BENCH = raw_input()
		SMILEI_BENCH_LIST = [ BENCH ]
elif BENCH in list_bench:
	SMILEI_BENCH_LIST = [ BENCH ]
elif glob.glob( SMILEI_BENCHS+BENCH ):
	BENCH = glob.glob( SMILEI_BENCHS+BENCH )    
        list_all = glob.glob(SMILEI_BENCHS+"tst*py")
	for b in BENCH:
		if b not in list_all:
			if VERBOSE:
				print "Input file "+b+" invalid."
			sys.exit(4)
        SMILEI_BENCH_LIST= []
        for b in BENCH:
                if b.replace(SMILEI_BENCHS,'') in list_bench:
                        SMILEI_BENCH_LIST.append( b.replace(SMILEI_BENCHS,'') )
        BENCH = SMILEI_BENCH_LIST
else:
	if VERBOSE:
		print "Input file "+BENCH+" invalid."
	sys.exit(4)

if VERBOSE :
	print ""
	print "The list of input files to be validated is:\n\t"+"\n\t".join(SMILEI_BENCH_LIST)
	print ""

# GENERIC FUNCTION FOR WORKDIR ORGANIZATION

import time
def date(BIN_NAME):
	statbin = os.stat(BIN_NAME)
	return statbin.st_ctime
def date_string(BIN_NAME):
	date_integer = date(BIN_NAME)
	date_time = time.ctime(date_integer)
	return date_time.replace(" ","-")
def workdir_archiv(BIN_NAME) :
	if os.path.exists(SMILEI_W):
		ARCH_WORKDIR = WORKDIR_BASE+'_'+date_string(SMILEI_W)
		os.rename(WORKDIR_BASE,ARCH_WORKDIR)
		os.mkdir(WORKDIR_BASE)

# PLATFORM-DEPENDENT INSTRUCTIONS FOR RUNNING PARALLEL COMMAND
def RUN_POINCARE(command, dir):
	# Create script
	with open(EXEC_SCRIPT, 'w') as exec_script_desc:
		print "ON POINCARE NOW"
		exec_script_desc.write(
			"# environnement \n"
			+"module load intel/15.0.0 intelmpi/5.0.1 hdf5/1.8.16_intel_intelmpi_mt python/anaconda-2.1.0 gnu gnu 2>&1 > /dev/null\n"
			+"unset LD_PRELOAD\n"
			+"export PYTHONHOME=/gpfslocal/pub/python/anaconda/Anaconda-2.1.0\n"
			+"# \n"
			+"# execution \n"
			+"export OMP_NUM_THREADS="+str(OMP)+"\n"
			+command+" \n"
			+"exit $?  "
		)
	# Run command
	COMMAND = "/bin/bash "+EXEC_SCRIPT+" > "+EXEC_SCRIPT_OUT+" 2>&1"
	try:
		check_call(COMMAND, shell=True)
	except CalledProcessError,e:
		# if execution fails, exit with exit status 2
		if VERBOSE :
			print  "Execution failed for command `"+command+"`"
			COMMAND = "/bin/bash cat "+WORKDIR+s+SMILEI_EXE_OUT
			try :
				check_call(COMMAND, shell=True)
			except CalledProcessError,e:
				print  "cat command failed"
				sys.exit(2)
		if dir==WORKDIR:
			os.chdir(WORKDIR_BASE)
			shutil.rmtree(WORKDIR)           
		sys.exit(2)
def RUN_JOLLYJUMPER(command, dir):
	EXIT_STATUS="100"
	exit_status_fd = open(dir+s+"exit_status_file", "w+")
	exit_status_fd.write(str(EXIT_STATUS))
	exit_status_fd.seek(0)
	# Create script
	with open(EXEC_SCRIPT, 'w') as exec_script_desc:
		NODES=((int(MPI)*int(OMP)-1)/24)+1
		exec_script_desc.write(
			"#PBS -l nodes="+str(NODES)+":ppn=24 \n"
			+"#PBS -q default \n"
			+"#PBS -j oe\n"
			+"export OMP_NUM_THREADS="+str(OMP)+" \n"
			+"export OMP_SCHEDULE=DYNAMIC \n"
			+"export KMP_AFFINITY=verbose \n"
			+"export PATH=$PATH:/opt/exp_soft/vo.llr.in2p3.fr/GALOP/beck \n"
			+"#Specify the number of sockets per node in -mca orte_num_sockets \n"
			+"#Specify the number of cores per sockets in -mca orte_num_cores \n"
			+"cd "+dir+" \n"
			+command+" \n"
			+"echo $? > exit_status_file \n"
		)
	# Run command
	COMMAND = "PBS_DEFAULT=llrlsi-jj.in2p3.fr qsub  "+EXEC_SCRIPT
	try:
		check_call(COMMAND, shell=True)
	except CalledProcessError,e:
		# if command qsub fails, exit with exit status 2
		exit_status_fd.close()  
		if dir==WORKDIR:
			os.chdir(WORKDIR_BASE)
			shutil.rmtree(WORKDIR)
		if VERBOSE :
			print  "qsub command failed: `"+COMMAND+"`"
			sys.exit(2)
	if VERBOSE:
		print "Submitted job with command `"+command+"`"
	while ( EXIT_STATUS == "100" ) :
		time.sleep(5)
		EXIT_STATUS = exit_status_fd.readline()
		exit_status_fd.seek(0)
	if ( int(EXIT_STATUS) != 0 )  :
		if VERBOSE :
			print  "Execution failed for command `"+command+"`"
			COMMAND = "cat "+WORKDIR+s+SMILEI_EXE_OUT
			try :
				check_call(COMMAND, shell=True)
			except CalledProcessError,e:
				print  "cat command failed"
				sys.exit(2)
		exit_status_fd.close()
		sys.exit(2)
def RUN_OTHER(command, dir):
		try :
			check_call(command, shell=True)
		except CalledProcessError,e:
			if VERBOSE :
				print  "Execution failed for command `"+command+"`"
			sys.exit(2)


# SET DIRECTORIES
if VERBOSE :
  print "Compiling Smilei"

os.chdir(SMILEI_ROOT)
WORKDIR_BASE = SMILEI_ROOT+"validation"+s+"workdirs"
SMILEI_W = WORKDIR_BASE+s+"smilei"
SMILEI_R = SMILEI_ROOT+s+"smilei"
if os.path.exists(SMILEI_R):
	STAT_SMILEI_R_OLD = os.stat(SMILEI_R)
else :
	STAT_SMILEI_R_OLD = ' '
COMPILE_ERRORS=WORKDIR_BASE+s+'compilation_errors'
COMPILE_OUT=WORKDIR_BASE+s+'compilation_out'
COMPILE_OUT_TMP=WORKDIR_BASE+s+'compilation_out_temp'

# Find commands according to the host
if JOLLYJUMPER in HOSTNAME :
	if 12 % OMP != 0:
		print  "Smilei cannot be run with "+str(OMP)+" threads on "+HOSTNAME
		sys.exit(4)  
	NPERSOCKET = 12/OMP
	COMPILE_COMMAND = 'make -j 12 > '+COMPILE_OUT_TMP+' 2>'+COMPILE_ERRORS  
	CLEAN_COMMAND = 'unset MODULEPATH;module use /opt/exp_soft/vo.llr.in2p3.fr/modulefiles; module load compilers/icc/16.0.109 mpi/openmpi/1.6.5-ib-icc python/2.7.10 hdf5 compilers/gcc/4.8.2 > /dev/null 2>&1;make clean > /dev/null 2>&1'
	RUN_COMMAND = "mpirun -mca orte_num_sockets 2 -mca orte_num_cores 12 -cpus-per-proc "+str(OMP)+" --npersocket "+str(NPERSOCKET)+" -n "+str(MPI)+" -x $OMP_NUM_THREADS -x $OMP_SCHEDULE "+WORKDIR_BASE+s+"smilei %s >"+SMILEI_EXE_OUT+" 2>&1"
	RUN = RUN_JOLLYJUMPER
elif POINCARE in HOSTNAME :
	#COMPILE_COMMAND = 'module load intel/15.0.0 openmpi hdf5/1.8.10_intel_openmpi python gnu > /dev/null 2>&1;make -j 6 > compilation_out_temp 2>'+COMPILE_ERRORS     
	#CLEAN_COMMAND = 'module load intel/15.0.0 openmpi hdf5/1.8.10_intel_openmpi python gnu > /dev/null 2>&1;make clean > /dev/null 2>&1'
	COMPILE_COMMAND = 'make -j 6 > '+COMPILE_OUT_TMP+' 2>'+COMPILE_ERRORS
	CLEAN_COMMAND = 'module load intel/15.0.0 intelmpi/5.0.1 hdf5/1.8.16_intel_intelmpi_mt python/anaconda-2.1.0 gnu gnu ; unset LD_PRELOAD ; export PYTHONHOME=/gpfslocal/pub/python/anaconda/Anaconda-2.1.0 > /dev/null 2>&1;make clean > /dev/null 2>&1'
	RUN_COMMAND = "mpirun -np "+str(MPI)+" "+WORKDIR_BASE+s+"smilei %s >"+SMILEI_EXE_OUT
	RUN = RUN_POINCARE
else:
	COMPILE_COMMAND = 'make -j4 > '+COMPILE_OUT_TMP+' 2>'+COMPILE_ERRORS
	CLEAN_COMMAND = 'make clean > /dev/null 2>&1'
	RUN_COMMAND = "export OMP_NUM_THREADS="+str(OMP)+"; mpirun -mca btl tcp,sm,self -np "+str(MPI)+" "+WORKDIR_BASE+s+"smilei %s >"+SMILEI_EXE_OUT
	RUN = RUN_OTHER

# CLEAN
# If the workdir does not contains a smilei bin, or it contains one older than the the smilei bin in directory smilei, force the compilation in order to generate the compilation_output
if not os.path.exists(WORKDIR_BASE):
	os.mkdir(WORKDIR_BASE)
if os.path.exists(SMILEI_R) and (not os.path.exists(SMILEI_W) or date(SMILEI_W)<date(SMILEI_R)):
	call(CLEAN_COMMAND , shell=True)

# COMPILE
try :
	# Remove the compiling errors files
	if os.path.exists(WORKDIR_BASE+s+COMPILE_ERRORS) :
		os.remove(WORKDIR_BASE+s+COMPILE_ERRORS)
	# Compile
	RUN( COMPILE_COMMAND, SMILEI_ROOT )
	os.rename(COMPILE_OUT_TMP, COMPILE_OUT)
	if STAT_SMILEI_R_OLD!=os.stat(SMILEI_R) or date(SMILEI_W)<date(SMILEI_R):
		# if new bin, archive the workdir (if it contains a smilei bin)  and create a new one with new smilei and compilation_out inside
		if os.path.exists(SMILEI_W):
			workdir_archiv(SMILEI_W)
		shutil.copy2(SMILEI_R,SMILEI_W)
		if COMPILE_ONLY:
			if VERBOSE:
				print  "Smilei validation succeed."
			exit(0)
	else: 
		if COMPILE_ONLY :
			if VERBOSE:
				print  "Smilei validation not needed."
			exit(0)
except CalledProcessError,e:
	# if compiling errors, archive the workdir (if it contains a smilei bin), create a new one with compilation_errors inside and exit with error code
	workdir_archiv(SMILEI_W)
	os.rename(COMPILE_ERRORS,WORKDIR_BASE+s+COMPILE_ERRORS)
	if VERBOSE:
		print "Smilei validation cannot be done : compilation failed." ,e.returncode
	sys.exit(3)
if VERBOSE: print ""


# DEFINE A CLASS TO CREATE A REFERENCE
class CreateReference(object):
	def __init__(self, bench_name):
		self.reference_file = SMILEI_REFERENCES+s+bench_name+".txt"
		self.data = {}
	
	def __call__(self, data_name, data, precision=None):
		self.data[data_name] = data
	
	def write(self):
		with open(self.reference_file, "w") as f:
			pickle.dump(self.data, f)
		size = os.path.getsize(self.reference_file)
		if size > 1000000:
			print "Reference file is too large ("+str(size)+"B) - suppressing ..."
			os.remove(self.reference_file)
			sys.exit(2)
		if VERBOSE:
			print "Created reference file "+self.reference_file

# DEFINE A CLASS TO COMPARE A SIMULATION TO A REFERENCE
class CompareToReference(object):
	def __init__(self, bench_name):
		try:
			with open(SMILEI_REFERENCES+s+bench_name+".txt", 'r') as f:
				self.data = pickle.load(f)
		except:
			print "Unable to find the reference data for "+bench_name
			sys.exit(1)
	
	def __call__(self, data_name, data, precision=None):
		# verify the name is in the reference
		if data_name not in self.data.keys():
			print "Reference quantity '"+data_name+"' not found"
			sys.exit(1)
		expected_data = self.data[data_name]
		# ok if exactly equal (including strings or lists of strings)
		try   :
			if expected_data == data: return
		except: pass
		# If numbers:
		try:
			double_data = np.array(np.double(data), ndmin=1)
			if precision is not None:
				error = np.abs( double_data-np.array(np.double(expected_data), ndmin=1) )
				max_error_location = np.unravel_index(np.argmax(error), error.shape)
				max_error = error[max_error_location]
				if max_error < precision: return
				print "Reference quantity '"+data_name+"' does not match the data (required precision "+str(precision)+")"
				print "Max error = "+str(max_error)+" at index "+str(max_error_location)
			else:
				if np.all(double_data == np.double(expected_data)): return
				print "Reference quantity '"+data_name+"' does not match the data"
		except:
			print "Reference quantity '"+data_name+"': unable to compare to data"
		print "Reference data:"
		print expected_data
		print "New data:"
		print data
		sys.exit(1)

# DEFINE A CLASS TO VIEW DIFFERENCES BETWEEN A SIMULATION AND A REFERENCE
class ShowDiffWithReference(object):
	def __init__(self, bench_name):
		try:
			with open(SMILEI_REFERENCES+s+bench_name+".txt", 'r') as f:
				self.data = pickle.load(f)
		except:
			print "Unable to find the reference data for "+bench_name
			sys.exit(1)
	
	def __call__(self, data_name, data, precision=None):
		import matplotlib.pyplot as plt
		plt.ion()
		print "Showing differences about '"+data_name+"'"
		print "--------------------------"
		# verify the name is in the reference
		if data_name not in self.data.keys():
			print "\tReference quantity not found"
			expected_data = None
		else:
			expected_data = self.data[data_name]
		print_data = False
		# try to convert to array
		try:
			data_float = np.array(data, dtype=float)
			expected_data_float = np.array(expected_data, dtype=float)
		# Otherwise, simply print the result
		except:
			print "\tQuantity cannot be plotted"
			print_data = True
			data_float = None
		# Manage array plotting
		if data_float is not None:
			if expected_data is not None and data_float.shape != expected_data_float.shape:
				print "\tReference and new data do not have the same shape"
				print_data = True
			elif data_float.size == 0:
				print "\t0D quantity cannot be plotted"
				print_data = True
			elif data_float.ndim == 1:
				nplots = 2
				if expected_data is None or data_float.shape != expected_data_float.shape:
					nplots = 1
				fig = plt.figure()
				fig.suptitle(data_name)
				print "\tPlotting in figure "+str(fig.number)
				ax1 = fig.add_subplot(nplots,1,1)
				ax1.plot( data_float, label="new data" )
				ax1.plot( expected_data_float, label="reference data" )
				ax1.legend()
				if nplots == 2:
					ax2 = fig.add_subplot(nplots,1,2)
					ax2.plot( data_float-expected_data_float )
					ax2.set_title("difference")
			elif data_float.ndim == 2:
				nplots = 3
				if expected_data is None:
					nplots = 1
				elif data_float.shape != expected_data_float.shape:
					nplots = 2
				fig = plt.figure()
				fig.suptitle(data_name)
				print "\tPlotting in figure "+str(fig.number)
				ax1 = fig.add_subplot(1,nplots,1)
				im = ax1.imshow( data_float )
				ax1.set_title("new data")
				plt.colorbar(im)
				if nplots > 1:
					ax2 = fig.add_subplot(1,nplots,2)
					im = ax2.imshow( expected_data_float )
					ax2.set_title("reference data")
					plt.colorbar( im )
				if nplots > 2:
					ax3 = fig.add_subplot(1,nplots,nplots)
					im = ax3.imshow( data_float-expected_data_float )
					ax3.set_title("difference")
					plt.colorbar( im )
				plt.draw()
				plt.show()
			else:
				print "\t"+str(data_float.ndim)+"D quantity cannot be plotted"
				print_data = True
		# Print data if necessary
		if print_data:
			if expected_data is not None:
				print "\tReference data:"
				print expected_data
			print "\tNew data:"
			print data


# RUN THE BENCHMARKS

for BENCH in SMILEI_BENCH_LIST :
	
	SMILEI_BENCH = SMILEI_BENCHS + BENCH
	
	# CREATE THE WORKDIR CORRESPONDING TO THE INPUT FILE AND GO INTO                
	WORKDIR = WORKDIR_BASE+s+'wd_'+os.path.basename(os.path.splitext(BENCH)[0])
	if not os.path.exists(WORKDIR):
		os.mkdir(WORKDIR)
	os.chdir(WORKDIR)
	
	WORKDIR += s+str(MPI)
	if not os.path.exists(WORKDIR):
		os.mkdir(WORKDIR)
	
	WORKDIR += s+str(OMP)
	EXECUTION = True
	if not os.path.exists(WORKDIR):
		os.mkdir(WORKDIR)
	elif GENERATE:
		EXECUTION = False
	
	os.chdir(WORKDIR)
	
	# RUN smilei IF EXECUTION IS TRUE
	if EXECUTION :
		if VERBOSE:
			print 'Running '+BENCH+' on '+HOSTNAME+' with '+str(OMP)+'x'+str(MPI)+' OMPxMPI'
		RUN( RUN_COMMAND % SMILEI_BENCH, WORKDIR )
	
	# CHECK THE OUTPUT FOR ERRORS
	errors = []
	search_error = re.compile('error', re.IGNORECASE)
	with open(SMILEI_EXE_OUT,"r") as fout:
		for line in fout:
			if search_error.search(line):
				errors += [line]
	if errors:
		print ""
		print("Errors appeared while running the simulation:")
		print("---------------------------------------------")
		for error in errors:
			print(error)
		sys.exit(2)
	
	# FIND THE VALIDATION SCRIPT FOR THIS BENCH
	validation_script = SMILEI_VALIDATION + "validate_"+BENCH
	if VERBOSE: print ""
	if not os.path.exists(validation_script):
		print "Unable to find the validation script "+validation_script
		sys.exit(1)
	
	# IF REQUIRED, GENERATE THE REFERENCES
	if GENERATE:
		if VERBOSE:
			print 'Generating reference for '+BENCH
		Validate = CreateReference(BENCH)
		execfile(validation_script)
		Validate.write()
	
	# OR PLOT DIFFERENCES WITH RESPECT TO EXISTING REFERENCES
	elif SHOWDIFF:
		if VERBOSE:
			print 'Viewing differences for '+BENCH
		Validate = ShowDiffWithReference(BENCH)
		execfile(validation_script)
	
	# OTHERWISE, COMPARE TO THE EXISTING REFERENCES
	else:
		if VERBOSE:
			print 'Validating '+BENCH
		Validate = CompareToReference(BENCH)
		execfile(validation_script)

        # CLEAN WORKDIRS, GOES HERE ONLY IF SUCCEED
	os.chdir(WORKDIR_BASE)
        shutil.rmtree( WORKDIR_BASE+s+'wd_'+os.path.basename(os.path.splitext(BENCH)[0]), True )
	
	if VERBOSE: print ""

print "Everything passed"
