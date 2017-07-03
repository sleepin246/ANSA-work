# PYTHON script
import os
import re
import ansa
import pickle
from ansa import batchmesh
from ansa import session
from ansa import utils
from ansa import base
from ansa import constants
from ansa import mesh
from ansa import script
from ansa import guitk

class work(object):
	
	def __init__(self):
		self.FixSets=[]
		self.PressureSets=[]
		self.CouplingSets=[]
		self.MPCSets=[]
		self.mpar=[]
		self.RefNodesSets=[]
		

#使用了re.split用以同时使用中英文逗号来区隔用户输入。使用判空、判断是否十进制输入来限制用户输入，而不使用try..except..finally..这样的通用错误调试功能。
	def CreateFixSets(self):
		buffer=(guitk.UserInput("Please specify the DOFs you want to fix, use , to seperate different sets"))
		if buffer==None:
			print("Cancel is selected,no sets generated!")
		else:
			buffer=re.split(',|，',buffer)
			for i in range(0,len(buffer)):
				if buffer[i].isdecimal():
					d={}
					d['Name']='Fix'+str(buffer[i])
					self.FixSets.append(base.CreateEntity(constants.ABAQUS, "SET", d))
				else:
					print("input error, please use the format XX,XX,XX to input, no user defined sets are generated.")
					return			
		return
		
#取消了原先指定ID才能建立Sets的限制，从而使用户可以建立任何ID的sets从而在任何时候都可以使用该功能。使用了不同的属性用来储存建立的sets。
	def CreateLoadSets(self):
		NumberOfUserDefinedSets=[0,0,0]
		buffer=(guitk.UserInput("Please specify the number of pressure areas,couplings and MPCs"))
		if buffer==None:
			print("Cancel is selected,no sets generated!")
		else:
			buffer=re.split(',|，',buffer)
			for i in range(0,min(len(buffer),3)):
				if buffer[i].isdecimal():
					NumberOfUserDefinedSets[i]=int(buffer[i])
				else:
					print("input error, please use the format XX,XX,XX to input, no user defined sets are generated.")
					return
			for i in range(NumberOfUserDefinedSets[0]):
				d={}
				d['Name']='PressureArea'+str(i+1)
				self.PressureSets.append(base.CreateEntity(constants.ABAQUS, "SET", d))
			for i in range(NumberOfUserDefinedSets[1]):
				d={}
				d['Name']='Coupling'+str(i+1)
				self.CouplingSets.append(base.CreateEntity(constants.ABAQUS, "SET", d))
			for i in range(NumberOfUserDefinedSets[2]):
				d={}
				d['Name']='MPC'+str(i+1)
				self.MPCSets.append(base.CreateEntity(constants.ABAQUS, "SET", d))	
			print("Sucessful!The sets are created!")
		
#基本逻辑是获取所需的如shell、solid的节点，然后在获取节点的坐标X,Y,Z并且取平均值，再按照平均值作为坐标建立Ref Node，并为其创建Set。该函数有几个难点：1.删除被用户删除的Sets，此处使用了i for i in if的语句，排除已被删除的sets；2.为Coupling和MPC分别定义，此处使用了Loadsets=Coupling/MPCSets来判断。本函数涉及多个工序较复杂，因此未设调用成功提示信息。
	def CreateCouplingAndMPCs(self):
		self.CouplingSets=[i for i in self.CouplingSets if str(i).find('id:0>')==-1 and i!=None]
		self.MPCSets=[i for i in self.MPCSets if str(i).find('id:0>')==-1 and i!=None]
		for LoadSets in [self.CouplingSets,self.MPCSets]:
			for i in LoadSets:
				BoundaryArea = base.CollectEntities(constants.ABAQUS,i,{'SHELL','FACE','CONS','NODE','SOLIDFACET','SOLID',})
				BoundaryHotPoints = base.CollectEntities(constants.ABAQUS,BoundaryArea,{'NODE','HOT POINT'})
				BoundaryNodes=base.CollectEntities(constants.ABAQUS,i,{'NODE',})
#				print(BoundaryNodes+BoundaryHotPoints)
				if BoundaryNodes+BoundaryHotPoints==[]:
#					print("The contents in the sets are not supported to create coupling and MPC automatically!")
					continue
				else:
#					print(BoundaryHotPoints)
					CardVals=('X','Y','Z')
					PointTempX=[]
					PointTempY=[]
					PointTempZ=[]
			
					for BHP in BoundaryNodes+BoundaryHotPoints:
						CardValues=base.GetEntityCardValues(constants.ABAQUS, BHP,CardVals)
						PointTempX.append(CardValues['X'])
						PointTempY.append(CardValues['Y'])
						PointTempZ.append(CardValues['Z'])
					BoundaryNodeCoord=[sum(PointTempX)/len(PointTempX),sum(PointTempY)/len(PointTempY),sum(PointTempZ)/len(PointTempZ)]
					RefNode=base.CreateEntity(constants.ABAQUS, "NODE",{'X':BoundaryNodeCoord[0],'Y':BoundaryNodeCoord[1],'Z':BoundaryNodeCoord[2]})
#					print("RefNode=",RefNode)
					if LoadSets==self.CouplingSets:		
						CRCP={'COUPLING':'*DISTRIBUTING','REF NODE':base.GetEntityCardValues(constants.ABAQUS,RefNode,{'ID'})['ID'],'SURF.TYPE':'NODE-BASED','DOF':123,'NSET':base.GetEntityCardValues(constants.ABAQUS,i,{'SID'})['SID'],'Name': 'FromSet'+str(base.GetEntityCardValues(constants.ABAQUS,i,{'Name'})['Name'])}
						base.CreateEntity(constants.ABAQUS,"COUPLING",CRCP)
						CRRNS1={'Name':'RefNode'+str(base.GetEntityCardValues(constants.ABAQUS,RefNode,{'ID'})['ID'])+'For'+str(base.GetEntityCardValues(constants.ABAQUS,i,{'Name'})['Name']),}
						RNS1Set=base.CreateEntity(constants.ABAQUS,"SET",CRRNS1)
#						print('CRRNS1=',CRRNS1)
						base.AddToSet(RNS1Set,RefNode)
						self.RefNodesSets.append(RNS1Set)
					elif LoadSets==self.MPCSets:
						base.AddToSet(i,RefNode)
						CRMPC={'TYPE': 'BEAM', 'NSET': base.GetEntityCardValues(constants.ABAQUS,i,{'SID'})['SID'], 'NODE0': base.GetEntityCardValues(constants.ABAQUS,RefNode,{'ID'})['ID'],'Name': 'FromSet'+str(base.GetEntityCardValues(constants.ABAQUS,i,{'Name'})['Name']),}
						base.CreateEntity(constants.ABAQUS,"MPC",CRMPC)
						CRRNS2={'Name':'RefNode'+str(base.GetEntityCardValues(constants.ABAQUS,RefNode,{'ID'})['ID'])+'For'+str(base.GetEntityCardValues(constants.ABAQUS,i,{'Name'})['Name']),}
						RNS2Set=base.CreateEntity(constants.ABAQUS,"SET",CRRNS2)
						base.AddToSet(RNS2Set,RefNode)
						self.RefNodesSets.append(RNS2Set)
		return 0
		
	def CreateCloadForRefNodes(self):
		self.RefNodesSets=[i for i in self.RefNodesSets if str(i).find('id:0>')==-1 and i!=None]
		for i in self.RefNodesSets:
			CloadVals={ 'by': 'set','STEP':1,'NSET':base.GetEntityCardValues(constants.ABAQUS,i,{'SID'})['SID'],'DOF': '1: Fx','magn(N)': '0','Name':'CloadOf'+str(base.GetEntityCardValues(constants.ABAQUS,i,{'Name'})['Name'])}
			base.CreateEntity(constants.ABAQUS,"CLOAD",CloadVals)
		self.PressureSets=[i for i in self.PressureSets if str(i).find('id:0>')==-1 and i!=None]
		
	def CreateDloadForPressureSets(self):
		self.PressureSets=[i for i in self.PressureSets if str(i).find('id:0>')==-1 and i!=None]
		for i in self.PressureSets:
			if base.CollectEntities(constants.ABAQUS, i, "__ALL_ENTITIES__",True)!=[]:
				PressureVals={ 'by': 'set','STEP':1,'ELSET':base.GetEntityCardValues(constants.ABAQUS,i,{'SID'})['SID'],'LOAD TYPE':'P','magn(EID)':0,'Name':'DloadOf'+str(base.GetEntityCardValues(constants.ABAQUS,i,{'Name'})['Name'])}
				base.CreateEntity(constants.ABAQUS,"DLOAD",PressureVals)
	
	def CreateBoundaryForRefNodes(self):
		self.RefNodesSets=[i for i in self.RefNodesSets if str(i).find('id:0>')==-1 and i!=None]
		for i in self.RefNodesSets:
			BoundaryVals={ 'by': 'set','NSET':base.GetEntityCardValues(constants.ABAQUS,i,{'SID'})['SID'],'DOF': '1','Magn(N)': '0','Name':'BoundaryOf'+str(base.GetEntityCardValues(constants.ABAQUS,i,{'Name'})['Name']),'TYPE':'DISPLACEMENT',}
			base.CreateEntity(constants.ABAQUS,"BOUNDARY",BoundaryVals)
			
	def CreateFixForFixSets(self):
		self.FixSets=[i for i in self.FixSets if str(i).find('id:0>')==-1 and i!=None]
		for i in self.FixSets:
			print(str(base.GetEntityCardValues(constants.ABAQUS,i,{'Name'})['Name'])[3:])
			BoundaryVals={ 'by': 'set','NSET':base.GetEntityCardValues(constants.ABAQUS,i,{'SID'})['SID'],'DOF': str(base.GetEntityCardValues(constants.ABAQUS,i,{'Name'})['Name'])[3:],'Magn(N)': '0','Name':'BoundaryOf'+str(base.GetEntityCardValues(constants.ABAQUS,i,{'Name'})['Name']),'TYPE':'DISPLACEMENT',}
			base.CreateEntity(constants.ABAQUS,"BOUNDARY",BoundaryVals)
					
	def BatchMesh(self):
		if os.path.isfile('work.ansa_mpar'):
			mpar='./work.ansa_mpar'
			if base.GetEntity(constants.ABAQUS, "BATCH_MESH_SESSION", 1)==None:
				NewScenario=batchmesh.GetNewMeshingScenario('Work','PIDS',)
			else:
				print("Already a Meshing Scenario!")
				NewScenario=base.GetEntity(constants.ABAQUS, "BATCH_MESH_SESSION_GROUP", 1)
			GetSession=base.GetEntity(constants.ABAQUS, "BATCH_MESH_SESSION", 1)
			SessionName = base.GetEntityCardValues(constants.ABAQUS,GetSession, ('Name',))
			print(SessionName)
			base.SetEntityCardValues(constants.ABAQUS,GetSession, {'Name':'WorkSession',})
			batchmesh.AddPartToMeshingScenario (base.CollectEntities(constants.ABAQUS, None, "__PROPERTIES__",True),NewScenario)
			batchmesh.ReadSessionMeshParams(GetSession,mpar)
			batchmesh.RunAllMeshingScenarios()
		else:
			print("please copy your work.ansa_mpar to the working directory first!")
		return

		
	def CreateStepOutPut(self):
		if base.GetEntity(constants.ABAQUS, "STEP", 1) ==None:
			WorkStep=base.CreateEntity(constants.ABAQUS, "STEP",{'STEP ID':'1','Name':'Work Step 1',})
		else:
			vals={'Name':'WorkStep'}
			WorkStep=base.GetEntity(constants.ABAQUS, "STEP", 1)
			base.SetEntityCardValues(constants.ABAQUS,WorkStep,vals)
#		if base.AbqStepCollectOutputRequests(WorkStep)==None:
			base.AbqStepInsertOutputRequest(WorkStep, "*OUTPUT",)
			base.AbqStepInsertOutputRequest(WorkStep, "*ELEMENT OUTPUT", "Identifying Keys","S,E","SECTION POINTS", "all")
			base.AbqStepInsertOutputRequest(WorkStep, "*NODE OUTPUT", "Identifying Keys","U","SECTION POINTS", "all")
			base.AbqStepInsertOutputRequest(WorkStep, "*CONTACT OUTPUT", "Identifying Keys","CFORCE",)
			base.AbqStepInsertOutputRequest(WorkStep, "*OUTPUT","PARAMETER","HISTORY",)
			NSETID=[]
			for i in range(len(self.RefNodesSets)):
				NSETID.append(base.GetEntityCardValues(constants.ABAQUS,self.RefNodesSets[i],{'SID'})['SID'])	
			base.AbqStepInsertOutputRequest(WorkStep, "*NODE OUTPUT","NSET",NSETID,"Identifying Keys","RF",)
		print("Your step and output has been created! Please create output after the ref node sets are created if the outputs for them are wanted be automatically generated!")
		
if __name__=='__main__':
    work()

	
	
	
	
	
	
	
	