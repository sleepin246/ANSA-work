import os
import ansa
import pickle
from ansa import constants
import work
from ansa import base
from ansa import utils
from ansa import guitk


###########################pickle模块##########################

#使用pickle对过程中创建的ANSA Entities进行缓存，缓存于"ANSA文件名.dump"中。需要注意的是，该缓存仅能储存本脚本自定义的按键所产生的ANSA Entities，因此，当用户使用ANSA内其他按键进行删除和创建entities时，并不能被缓存所记录。
#当用户删除自定义按键生成的entities时，储存于缓存中的entities将变为（deleted,id=0）的状态；脚本对用户删除自定义entities进行了检测，并会自动删除已经为deleted状态的entities，从而避免发生缓存中和实际中的entities不一致而出现问题。

def WritingWorkPickle(dump):
	DumpFileName=os.path.split(base.GetGeneralComment())[1]+".dump"
	f = open(DumpFileName, 'wb')
	pickle.dump(dump,f)
	f.close()

def ReadingWorkPickle():
	DumpFileName=os.path.split(base.GetGeneralComment())[1]+".dump"
	f = open(DumpFileName, 'rb')
	dump = pickle.load(f)
	f.close()
#		print("Work =",Work)
	return dump
###########################pickle模块###########################

#####################Dump文件路径选择和检测######################

#由于缓存文件于ANSA文件存在同一目录为最合适的选择，因此在使用任何按钮之前，均需要首先获取ANSA文件的路径。若要获取ANSA文件的路径，若此时ANSA文件还未保存，则会要求首先保存文件，从而记录其路径，路径存在ANSA的GeneralComment中以备后用；若已经保存文件，则GeneralComment中可以检测到其路径，脚本会使用os.chdir()转到其路径。在每一个按钮中，都设置了检查路径这一项，确保每次打开ANSA时，都可以进行检测从而始终在正确的路径下工作。

def SelectPathAndSaveFile():
	print("Save your file first!Pelase slect the path to save your .ansa file!")
	file=utils.SelectSaveFile("*.ansa")
	return file

#@ansa.session.defbutton('Work', 'CheckPath')
def CheckOrCreatePath():
#	print("you are now at:",os.getcwd())
	if base.GetGeneralComment()=="":
		FullFilePath=SelectPathAndSaveFile()
		ansa.base.SetGeneralComment(str(FullFilePath[0]))
		DumpDir=os.path.split(FullFilePath[0])[0]
		os.chdir(DumpDir)
	else:
		os.chdir(os.path.split(base.GetGeneralComment())[0])
	if os.path.isfile(os.path.split(base.GetGeneralComment())[1]+".dump"):
		return
	else:
		mywork=work.work()
		WritingWorkPickle(mywork)
		
###################Dump文件路径选择和检测#########################	

##########################工作模块###############################
	
#工作模块包括了建立Abaqus Standard常用静力分析所需的功能。使用工作模块进行工作时，CreateXXXSets会首先创建有规则的Set名字，比如Set:"Coupling1","PressureArea2","MPC3"等，其中英文表示了该set中所存放的内容的用途，比如Coupling1 set内的内容将会用于创建Coupling；数字代表编号，如果需要创建3个Coupling，就会有Coupling1,2,3。当Sets被创建后，用户需要使用modify contents手工进行sets内容的指定。指定后，所有有内容的sets可以通过点击相应的按钮来创建对应的属性。按钮的顺序按照一个case的一般工作流程。

#创建施加力或位移的sets，包括PressureArea，Coupling和MPC sets。点选后，会跳出提示框，用户需要以XX,XX,XX的格式分别指定所需要的P,C,M的数量。
@ansa.session.defbutton('Work', 'CreateLoadSets')
def myCreateLoadSets():
	CheckOrCreatePath()
	mywork=ReadingWorkPickle()
	mywork.CreateLoadSets()
	WritingWorkPickle(mywork)

#创建需要约束DoFs的sets。点选后，跳出提示框，要求用户输入所需要约束的DoFs，以数字表达，可以以","隔开，表示同时创建两个sets。
@ansa.session.defbutton('Work', 'CreateFixSets')
def myCreateFixSets():
	CheckOrCreatePath()
	mywork=ReadingWorkPickle()
	mywork.CreateFixSets()
	WritingWorkPickle(mywork)
	
#创建Coupling和MPC sets对应的Coupling和MPC。Coupling和MPC sets中，可以包含所有类型，包括Cons,Face,Node,Shell,Solid和SolidFacet，同一个set内可以包括不同类型的entities。所建立的Coupling或MPC的ref node坐标为set内所有node/hot point的中点。将为RefNode单独创建set，其名字为“RefNode+Node ID+For+Coupling/MPC”，以作后用。
@ansa.session.defbutton('Work', 'CreateCouplingAndMPCs')
def myCreateCouplingAndMPCs():
	CheckOrCreatePath()
	mywork=ReadingWorkPickle()
	mywork.CreateCouplingAndMPCs()
	WritingWorkPickle(mywork)

#为所有前述RefNodeSets建立Cload模板，其Magn为0，方向初始为Fx。建立后需手动修改数值和方向等。其名称为NodeID和关联Set名。
@ansa.session.defbutton('Work', 'CreateCloadForRefNodes')
def myCreateCloadForRefNodes():
	CheckOrCreatePath()
	mywork=ReadingWorkPickle()
	mywork.CreateCloadForRefNodes()
	WritingWorkPickle(mywork)

#为所有前述RefNodeSets建立强制位移模板，其Magn为0，DOF初始为1。 建立后需手动修改数值和方向等。其名称为NodeID和关联Set名。	
@ansa.session.defbutton('Work', 'CreateBoundaryForRefNodes')	
def myCreateBoundaryForRefNodes():	
	CheckOrCreatePath()
	mywork=ReadingWorkPickle()
	mywork.CreateBoundaryForRefNodes()
	WritingWorkPickle(mywork)

#为创立的FixSets建立Boundary，DOF为Set名中制定的DOF。如有必要需手动修改卡片。
@ansa.session.defbutton('Work', 'CreateFixForFixSets')	
def myCreateFixForFixSets():	
	CheckOrCreatePath()
	mywork=ReadingWorkPickle()
	mywork.CreateFixForFixSets()
	WritingWorkPickle(mywork)	

#首先需粘贴work.ansa_mpar到ANSA文件的同一目录下。点选后会自动创立Batch Mesh Session并且运行。因此如有必要，提前手动修改work.ansa_mpar内的参数。
@ansa.session.defbutton('Work', 'BatchMesh')	
def myBatchMesh():	
	CheckOrCreatePath()
	mywork=ReadingWorkPickle()
	mywork.BatchMesh()
	WritingWorkPickle(mywork)	

#为PressureAreaSets建立Dload。需要先有网格才能建立，否则会返回empty set错误。	
@ansa.session.defbutton('Work', 'CreateDloadForPressureSets')	
def myCreateDloadForPressureSets():
	CheckOrCreatePath()
	mywork=ReadingWorkPickle()
	mywork.CreateDloadForPressureSets()
	WritingWorkPickle(mywork)

#建立常用Abaqus Field Output，如E,S,U,CFORCE等。为RefNodeSets建立History Output,默认输出为RF。
@ansa.session.defbutton('Work', 'CreateStepOutputs')
def myCreateStepOutPut():
	CheckOrCreatePath()
	mywork=ReadingWorkPickle()
	mywork.CreateStepOutPut()
	WritingWorkPickle(mywork)

#输出Inp文件，需用户指定其名称（无需输入.inp)；如未指定，使用General Comments中的ANSA文件名；若General Comments同样为空，使用'ANSAAutoExported.inp'为文件名。
@ansa.session.defbutton('Work', 'ExportInp')
def ExportInp():
	InpName=guitk.UserInput("Please specify the name of the .inp file!Default is the same as the .ansa file!")
	if InpName==None:
		print("Cancel is selected,no file exported!")
		return
	elif InpName=='':
		if base.GetGeneralComment()!="":
			InpName=os.path.split(base.GetGeneralComment())[1][:-5]
		else:
			InpName='ANSAAutoExported'
	base.OutputAbaqus(filename=InpName+'.inp', disregard_includes="on")
	
##########################工作模块###############################