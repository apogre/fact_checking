# ---- Cleanup everything before start ----
rm(list = ls())
gc()

### Find true capital-state pairs from all possible capital-state pairs

# ---- GBSERVER API ----
source("./experimentAPI.R")

# ---- INPUT and CONFIGURATIONS ----

EDGE_TYPE_FILE = "../data/infobox.edgetypes" # Example : "../data/lobbyist.edgetypes"
INPUT_FILE = "../KGMiner_data/training_data.csv" # Example : "../facts/lobbyist/firm_payee.csv" col 1 and 2 are ids and 3 is label
INPUT_FILE_TEST = "../KGMiner_data/test_data.csv"
# INPUT_FILE_FALSE = "../facts/state_capital_false.csv"
setwd("/home/apradhan/proj/fact_checking/KGMiner/Rscript")
poi = read.csv("../KGMiner_data/poi.csv", header = FALSE)
poi_val = as.numeric(poi[1])
# poi_text = as.character(poi[2][1])
CLUSTER_SIZE = 48 # Number of workers in gbserver
FALSE_PER_TRUE = 4
DISCARD_REL = poi_val
print(DISCARD_REL)
ASSOCIATE_REL = c(404)
max_depth = 3

# if (ncol(az) < 3)
#   az$label <- T
# colnames(az) <- c("src","dst","label")
# testdata1<-head(experiment.test$raw)
# testdata2<-tail(experiment.test$raw)
# test<-rbind(testdata1,testdata2)
# 
# predict(experiment.test$model,newdata = test_set)
# predict(experiment.test$model,newdata = test)
# 
# predict(experiment.test$model,newdata = test, type = c("class"))

# ---- Load edge type file ----

mapfile <- read.csv(EDGE_TYPE_FILE, sep="\t", header=F)
mapfile$V1 <- as.numeric(mapfile$V1)
mapfile$V2 <- as.character(mapfile$V2)

# ---- Init workers ----

cl <- makeCluster(CLUSTER_SIZE)
clusterExport(cl = cl, varlist=c("adamic_adar", "semantic_proximity", "ppagerank", "heter_path",  "max_depth",
                                 "preferential_attachment", "katz", "pcrw", "heter_full_path", "meta_path",
                                 "multidimensional_adamic_adar", "heterogeneous_adamic_adar",
                                 "connectedby", "rel_path", "truelabeled", "falselabeled", "str_split",
                                 "as.numeric", "request","DISCARD_REL"), envir = environment())

# ---- Load input data ----
dat.true <- read.csv(INPUT_FILE,header=F)

if (ncol(dat.true) < 3)
  dat.true$label <- T

if(nrow(dat.true)<15)
  FALSE_PER_TRUE = 1
# ---- Construct false labeled data -----
set.seed(233)

#TODO: reformat this so it is universal and file independent
dat.false <- rbind.fill(apply(dat.true, 1, function(x){
  candidates <- unique(dat.true[which(dat.true[,1] != x[1]), 2])
  candidates <- unlist(lapply(candidates, function(y){
    if(length(which(dat.true[,1] == x[1] & dat.true[,2] == y) != 0)) {
      return(NULL)
    }
    return(y)
  }))
  return(data.frame(src=x[1],
                    dst=sample(candidates, FALSE_PER_TRUE),
                    label=F))
}))

# ---- Load test input data ----
dat.test <- read.csv(INPUT_FILE_TEST,header = FALSE)

if (ncol(dat.test) < 3)
  dat.test$label <- T

colnames(dat.true) <- c("src","dst","label")
colnames(dat.test) <- c("src","dst","label")

dat <- rbind(dat.true, dat.false)

elapsed.time <- data.frame()

## Test Method

experiment.fullpath.test <- eval.fullpath.test(dat, DISCARD_REL)
# write.csv(experiment.fullpath.test$raw, "../result/city/capital_state_all.fullpath.test.csv", row.names=F)

# print("FULL PATH")
# print(experiment.fullpath.test$eval)

elapsed.time <- rbind(elapsed.time, data.frame(method="fullpath.test",
                                               elapsed = experiment.fullpath.test$elapsed[3] * CLUSTER_SIZE / nrow(dat)))

experiment.test <- eval.test(dat, DISCARD_REL)
# dim(az)
# dat<-az

# write.csv(experiment.test1$raw, "result/city/capital_state.predict.csv", row.names=F)

write.csv(experiment.test$raw, "../result/training_features.csv", row.names=F)
# print("PREDICATE PATH")
# print(experiment.test$eval)

elapsed.time <- rbind(elapsed.time, data.frame(method="test",
                                               elapsed = experiment.test$elapsed[3] * CLUSTER_SIZE / nrow(dat)))


dat<-dat.test
experiment.test1 <- eval.test1(dat, DISCARD_REL)
write.csv(experiment.test1$raw, "../result/test_features_raw.csv", row.names=F)

training_set = as.data.frame(experiment.test$raw)
test_set_raw = as.data.frame(experiment.test1$raw)
test_set = data.frame(matrix(0,nrow=nrow(test_set_raw),ncol=ncol(training_set)))
colnames(test_set) = colnames(training_set)

for (col in colnames(test_set)){
  if(col %in% colnames(test_set_raw)){
    # print(col)
    test_set[col]<-test_set_raw[col]
  }
}
prob=predict(experiment.test$model,newdata = test_set)
prob_score = prob
print('Proability of LinK Prediction:')
print(prob_score)
# prob_score =0.55
MyData = as.data.frame(c(poi[2][1],prob_score))
colnames(MyData) <- c("poi", "score")
write.csv(MyData, file = "/home/apradhan/proj/fact_checking/KGMiner/KGMiner_data/predicate_probability.csv",row.names=FALSE)
q()


## Adamic Adar

experiment.aa <- eval.aa(dat, DISCARD_REL)
write.csv(experiment.aa$raw, "../result/city/capital_state_all.aa.csv", row.names=F)

elapsed.time <- rbind(elapsed.time, data.frame(method="aa",
                                               elapsed = experiment.aa$elapsed[3] * CLUSTER_SIZE / nrow(dat)))

## Semantic Proximity

experiment.sp <- eval.sp(dat, DISCARD_REL)
write.csv(experiment.sp$raw, "../result/city/capital_state_all.sp.csv", row.names=F)

elapsed.time <- rbind(elapsed.time, data.frame(method="sp",
                                               elapsed = experiment.sp$elapsed[3] * CLUSTER_SIZE / nrow(dat)))

## Personalized PageRank

experiment.ppr <- eval.ppr(dat, DISCARD_REL)
write.csv(experiment.ppr$raw, "../result/city/capital_state_all.ppr.csv", row.names=F)

elapsed.time <- rbind(elapsed.time, data.frame(method="ppr",
                                               elapsed = experiment.ppr$elapsed[3] * CLUSTER_SIZE / nrow(dat)))


## Preferential Attachment

experiment.pa <- eval.pa(dat, DISCARD_REL)
write.csv(experiment.pa$raw, "../result/city/capital_state_all.pa.csv", row.names=F)

elapsed.time <- rbind(elapsed.time, data.frame(method="pa",
                                               elapsed = experiment.pa$elapsed[3] * CLUSTER_SIZE / nrow(dat)))



## Katz

experiment.katz <- eval.katz(dat, DISCARD_REL)
write.csv(experiment.katz$raw, "../result/city/capital_state_all.katz.csv", row.names=F)

elapsed.time <- rbind(elapsed.time, data.frame(method="katz",
                                               elapsed = experiment.katz$elapsed[3] * CLUSTER_SIZE / nrow(dat)))



## AMIE

experiment.amie <- eval.amie(dat, ASSOCIATE_REL)
write.csv(experiment.amie$raw, "../result/city/capital_state_all.amie.csv", row.names=F)

elapsed.time <- rbind(elapsed.time, data.frame(method="amie",
                                               elapsed = experiment.amie$elapsed[3] * CLUSTER_SIZE / nrow(dat)))


experiment.pcrwamie <- eval.pcrw(dat, c(404))
write.csv(experiment.pcrwamie$raw, "../result/city/capital_state_all.pcrwamie.csv", row.names=F)

elapsed.time <- rbind(elapsed.time, data.frame(method="pcrw",
                                               elapsed = experiment.pcrwamie$elapsed[3] * CLUSTER_SIZE / nrow(dat)))

write.csv(elapsed.time, paste("../result/city/capital_state_all.elapsed.csv",sep=""), row.names=F)

stopCluster(cl)

experiment.simrank <- read.csv("../facts/state_capital.simrank.csv", header=F)
colnames(experiment.simrank) <- c("src", "dst", "score")
experiment.simrank <- merge(experiment.simrank, dat)[, c("label","score")]
experiment.simrank <- eval.df(experiment.simrank)
write.csv(experiment.simrank$raw, "../result/city/state_capital_all.simrank.csv", row.names=F)

