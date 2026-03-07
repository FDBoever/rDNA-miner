

#libraries
message("-- Loading packages")
suppressPackageStartupMessages(library('DECIPHER'))
#suppressPackageStartupMessages(library('ensembleTax'))
suppressPackageStartupMessages(library('Biostrings'))

out_dir <- if (length(args) >= 5 && nchar(args[5]) > 0 && args[5] != "None") args[5] else getwd()
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# Default paths
pr2_default   <- "./db/pr2/pr2_version_5.0.0_SSU.decipher.trained.rds"
silva_default <- "./db/silva/SILVA_SSU_r138_2019.RData"

# If user gave a 3rd/4th arg, check whether it's != "None"
if (length(args) >= 4 && args[3] != "None") {
  pr2_training <- args[3]
} else {
  pr2_training <- pr2_default
}

if (length(args) >= 5 && args[4] != "None") {
  silva_training <- args[4]
} else {
  silva_training <- silva_default
}

message("-- Loading trainingset")
if (args[2] == "pr2") {
  message("    + ", pr2_training)
  message("-- Reading RDS")
  trainingSet <- readRDS(pr2_training)
} else if (args[2] == "silva") {
  message("    + ", silva_training)
  message("-- Reading RData")
  load(silva_training)
} else {
  stop("args[2] must be 'pr2' or 'silva'")
}


# Read sequences to assign
#input_fasta <- "./re-assembly-megahit-cm/cm-analyse/extracted_sequences_SSU_rRNA_eukarya.fasta"

input_fasta <- args[1]
message("-- Reading Fasta")
message("    + ", input_fasta)

seq <- readDNAStringSet(input_fasta)

if (length(seq) == 0) {
  message("No sequences found in file: ", input_fasta)
  message("Exiting gracefully without processing.")
  quit(status = 0)  # Exit normally (no error)
}

# Otherwise, proceed normally
message("Found ", length(seq), " sequences.")


message("-- Classify with DECIPHER")
# Get the taxonomy from the training set
ids <- IdTaxa(seq,
              trainingSet,
              type="extended",
              strand="top",
              threshold=0)

message("-- Generating output file(s)")
#df <- idtax2df(tt = ids, db = "pr2", ranks = NULL, boot = 0, rubric = NULL, return.conf = FALSE)
df <- data.frame()

for(i in 1:length(ids)){
  df<-rbind(df,c('query'=names(ids[i][1]),
                 'confidence'=paste(ids[[i]]$confidence,collapse=";"),
                 'taxon'=paste(ids[[i]]$taxon,collapse=";")
  )
  )
}

colnames(df) <- c('query','confidence','taxon')

#separate them by taxon level for better handling
if(args[2]=='pr2'){
  tax.string <- c("root","domain","supergroup","division",'subdivision',"class","order","family","genus","species")
}
if(args[2]=='silva'){
  tax.string <- c("root","domain","phylum","class","order","family","genus","species")
}

df <- df %>%
  dplyr::mutate(taxon_long = taxon) %>%
  dplyr::mutate(confidence_long = confidence) %>%
  tidyr::separate(taxon, into = tax.string, sep=';') %>%
  tidyr::separate(confidence,into = paste0(tax.string,'_confidence'), sep=';' )

df

message("-- Saving output file(s)")
outfile <- file.path(out_dir, paste0("decipher_", args[2], ".tsv"))
write.table(df, file = outfile, sep = "\t", row.names = FALSE, quote = FALSE)
message("-- Wrote: ", outfile)