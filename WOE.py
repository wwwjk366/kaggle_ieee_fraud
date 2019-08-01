# Author : Bertrand Brelier
# Class to convert Categorical and numeric variables in Weight of Evidence
# Version 2.3
import numpy as np
import pandas as pd

class ConvertCategoricalFeatures():
    #Class to convert categorical features to WOE for binary classification problem (target = 0 or 1)
    def __init__(self,target,Features):
        self.target = target
        self.Model = {}
        self.Features = Features
    def train(self,traindf):
        NPositive=traindf[traindf[self.target]==1].shape[0]
        NNegative=traindf[traindf[self.target]==0].shape[0]
        for feature in self.Features:
            results = traindf[[feature,self.target]].fillna("None").groupby([feature]).agg(['sum','count'])
            results = results.reset_index()
            results.columns=[feature,"Positive","Count"]
            results["Negative"]=results["Count"]-results["Positive"]
            results["CountPositive"] = results["Positive"]
            #Replace 0 with 1 to avoid infinite log                                                                                                          
            results.loc[results.Negative == 0, 'Negative'] = 1
            results.loc[results.Positive == 0, 'Positive'] = 1
            #Distribution Positive (Good)                                                                                                                    
            results["DG"]=results["Positive"]*1./NPositive
            #Distribution Negative (Bad)                                                                                                                     
            results["DB"]=results["Negative"]*1./NNegative
            #WOE                                                                                                                                             
            results["WOE"]=np.log(results["DG"]/results["DB"])
            results.loc[results.Count <= 10, 'WOE'] = 0
            results.loc[results.CountPositive <= 1, 'WOE'] = results["WOE"].min()
            results = results[[feature,'WOE']]
            self.Model[feature] = dict(zip(results[feature], results.WOE))
    def transform(self,testdf):
        #In case new values are found, needs to impute 0 for WOE
        for feature in self.Features:
            testdf.fillna({feature: "None"}, inplace=True)
            #testdf[feature]=testdf[feature].fillna("None")
            #testdf.loc[feature].fillna("None", inplace=True)
            ListofValues = list(set(testdf[feature].values))
            for omega in ListofValues:
                if omega not in self.Model[feature]:
                    self.Model[feature][omega]=0.
        return testdf.replace(self.Model)

    
class ConvertContinuousFeatures():
    #Class to convert continuous features to WOE for binary classification problem (target = 0 or 1)
    def __init__(self,target,Features,NBins):
        self.target = target
        self.Model = {}
        self.Features = Features
        self.NBins = NBins
        self.BinModel = {}
    def train(self,traindf):
        NPositive=traindf[traindf[self.target]==1].shape[0]
        NNegative=traindf[traindf[self.target]==0].shape[0]
        for feature in self.Features:
            tmpdf = traindf[[feature,self.target]].copy(deep=True)
            List = sorted(list(filter(lambda x:not np.isnan(x),tmpdf[feature].values)))
            Len = len(List)
            BinsLim = [-np.inf]
            for omega in range(1,self.NBins):
                Value = List[int(omega * Len / self.NBins)]
                if Value not in BinsLim:
                    BinsLim.append( Value )
            BinsLim.append(np.inf)
            self.BinModel[feature] = BinsLim
            tmpdf["bin"] = pd.cut(tmpdf[feature], self.BinModel[feature], labels=range(1,len(self.BinModel[feature])))
            tmpdf["bin"] = tmpdf["bin"].cat.add_categories([-1])
            tmpdf["bin"].fillna(-1, inplace=True) 
            results = tmpdf[["bin",self.target]].groupby(["bin"]).agg(['sum','count'])
            results = results.reset_index()
            results.columns=["bin","Positive","Count"]
            results["Negative"]=results["Count"]-results["Positive"]
            results["CountPositive"] = results["Positive"]
            #Replace 0 with 1 to avoid infinite log                                                                                                          
            results.loc[results.Negative == 0, 'Negative'] = 1
            results.loc[results.Positive == 0, 'Positive'] = 1
            #Distribution Positive (Good)                                                                                                                    
            results["DG"]=results["Positive"]*1./NPositive
            #Distribution Negative (Bad)                                                                                                                     
            results["DB"]=results["Negative"]*1./NNegative
            #WOE                                                                                                                                             
            results["WOE"]=np.log(results["DG"]/results["DB"])
            results.loc[results.Count <= 10, 'WOE'] = 0
            results.loc[results.CountPositive <= 1, 'WOE'] = results["WOE"].min()
            results = results[["bin",'WOE']]
            self.Model[feature] = dict(zip(results["bin"], results.WOE))
    def transform(self,testdf):
        tmpdf = testdf.copy(deep=True)
        for feature in self.Features:
            tmpdf[feature] = pd.cut(tmpdf[feature], self.BinModel[feature], labels=range(1,len(self.BinModel[feature])))
            tmpdf[feature] = tmpdf[feature].cat.add_categories([-1])
            tmpdf[feature].fillna(-1, inplace=True) 
        return tmpdf.replace(self.Model)
        #return tmpdf.dtypes
