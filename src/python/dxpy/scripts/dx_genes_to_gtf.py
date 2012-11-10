#!/usr/bin/env python

import dxpy
import argparse
import sys

global nullInt
nullInt = -2**31
global nullFloat
nullFloat = float(nullInt)

parser = argparse.ArgumentParser(description="Export Genes object to GTF File")
parser.add_argument("genes_id", help="Genes table id to read from")
parser.add_argument("--output", dest="file_name", default=None, help="Name of file to write GTF to.  If not given GTF file will be printed to stdout.")

def main(**kwargs):

    if len(kwargs) == 0:
        opts = parser.parse_args(sys.argv[1:])
    else:
        opts = parser.parse_args(kwargs)

    if opts.genes_id == None:
        parser.print_help()
        sys.exit(1)
        
    if opts.file_name != None:
        outputFile = open(opts.file_name, 'w')
    else:
        outputFile = None
        

    if opts.genes_id == None:
        parser.print_help()
        sys.exit(1)

    tableId = opts.genes_id
    table = dxpy.DXGTable(tableId)
    
    transcripts = {}
    genes = {}
    
    acceptedTypes = {"CDS":"CDS", "start_codon": "start_codon", "stop_codon": "stop_codon", "5' UTR": "5UTR", "3' UTR": "3UTR", "intergenic":"inter", "intergenic_conserved":"inter_CNS", "exon":"exon"}
    
    for row in table.iterate_rows(want_dict=True):
        if row["type"] == "gene":
            if genes.get(row["span_id"]) == None:
                genes[row["span_id"]] = str(row["span_id"])
                if row.get("gene_id") != None:
                    if row["gene_id"] != "":
                        genes[row["span_id"]] = row["gene_id"]
                if row.get("name") != None and genes[row["span_id"]] == str(row["span_id"]):
                    if row["name"] != '':
                        genes[row["span_id"]] = row["name"]
            else:
                raise dxpy.AppError("Error: span_id was not unique, in violation of the type spec for Genes. As a result, some gene_id data may be overwritten")
    
        if row["type"] == "transcript":
            if transcripts.get(row["span_id"]) == None:
                transcriptInfo = {"name": str(row["span_id"])}
                if row.get("gene_id") != None:
                    if row["transcript_id"] != '':
                        transcriptInfo["name"] = row["transcript_id"]
                if row.get("name") != None and transcriptInfo["name"] == str(row["span_id"]):
                    if row["name"] != '':
                        transcriptInfo["name"] = row["name"]
                transcriptInfo['parent'] = row["parent_id"]
                transcriptInfo['gene'] = ''
                transcripts[row["span_id"]] = transcriptInfo
            else:
                raise dxpy.AppError("Error: span_id was not unique, in violation of the type spec for Genes. As a result, some transcript_id data may be overwritten")
    
    for k, v in transcripts.iteritems():
        if genes.get(v["parent"]) != None:
            transcripts[k]["gene"] = genes[v["parent"]]
        
    warnedGeneId = False
    warnedTranscriptId = False
        
    for row in table.iterate_rows(want_dict=True):
        if acceptedTypes.get(row["type"]) != None:
            reservedColumns = ["chr", "lo", "hi", "span_id", "type", "strand", "score", "is_coding", "parent_id", "frame", "source", "gene_id", "transcript_id", "__id__"]
            attributes = ""
            
            transcriptId = ''
            geneId = ''
            try:
                transcriptId = transcripts[row["parent_id"]]["name"]
                
            except:
                if not warnedTranscriptId:
                    print "Warning, at least one position had a transcriptId that could not be determined. Future warnings of this type will not be printed"
                    print "Offending position - Chr: " + row["chr"] + " lo: " + str(row["lo"]) + " hi: "
                    warnedTranscriptId = True
    
            try:
                geneId = transcripts[row["parent_id"]]["gene"]
            except:
                if not warnedGeneId:
                    print "Warning, at least one position had a geneId that could not be determined. Future warnings of this type will not be printed"
                    print "Offending position - Chr: " + row["chr"] + " lo: " + str(row["lo"]) + " hi: "
                    warnedGeneId = True
    
            attributes += "gene_id " + '"' + geneId + '"' + ";"
            attributes += " transcript_id " + '"' + transcriptId + '"' +";"
    
            for k, v in row.iteritems():
                if k not in reservedColumns and v != '':
                    attributes += " " + k + " " + '"'+str(v)+'";'
            chromosome = row["chr"]
            lo = str(row["lo"] + 1)
            hi = str(row["hi"] + 1)
            typ = row["type"]
            strand = row["strand"]
            if strand == '':
                strand = '.'
            if row["frame"] == -1:
                frame = '.'
            else:
                frame = str(row["frame"])
            source = '.'
            
            if row["score"] == nullFloat or row["score"] == nullFloat + 1.0:
                score = "."
            else:
                score = str(row["score"])
            
            if row.get("source") != None:
                if row["source"] !=  '':
                    source = row["source"]
            result = "\t".join([chromosome, source, typ, lo, hi, score, strand, frame, attributes.rstrip(";")])+"\n"
            if outputFile != None:
                outputFile.write(result)
            else:
                sys.stdout.write(result)

main()