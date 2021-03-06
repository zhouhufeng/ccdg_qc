import hail as hl
import sys
import timeit

start = timeit.default_timer()

hl.init(log='/hail.log', min_block_size=2048, default_reference='GRCh38')


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# define files
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# input
vds_immune_file = 'gs://ccdg-qc-multi/CCDG_Immune_IBD_T1D_AA_WGS/vds/CCDG_Immune_IBD_T1D_AA_WGS.vds'
pheno_file = 'gs://ccdg-qc-multi/data/IBD/v2/immune_ccdg_wgs_manifest_march2018_formatted.tsv'
ibdvars_file = 'gs://ccdg-qc-multi/data/IBD/v2/ibdvars.txt'
manuelvars_file = 'gs://ccdg-qc-multi/data/IBD/manuel_genes.txt'
#pca_afr_file = 'gs://ccdg-qc-multi/qc_measures/pca/allchr/perpop/pca_scores_AFR.tsv'
#pc_global_file = 'gs://ccdg-qc-multi/qc_measures/pca/allchr/pca_scores.tsv'
#predicted_pop_file = 'gs://ccdg-qc-multi/qc_measures/pca/allchr/predicted_populations.tsv'
#samples_to_keep_file = 'gs://ccdg-qc-multi/qc_measures/allchr/01_sample_qc_keep.txt'


# output
#filtered_vds_immune_file = 'gs://ccdg-qc-multi/data/IBD/v2/filtered_immune.vds'
filtered_vds_immune_file2 = 'gs://ccdg-qc-multi/data/IBD/v2/filtered_immune2.vds'
ibd_vars_table_file = 'gs://ccdg-qc-multi/data/IBD/v2/vartable.tsv'
logreg_file = 'gs://ccdg-qc-multi/data/IBD/v2/logreg_results.tsv'
logreg_pop_file = 'gs://ccdg-qc-multi/data/IBD/v2/logreg_results_'
samples_file = 'gs://ccdg-qc-multi/data/IBD/v2/samples_file.tsv'
plink_file = 'gs://ccdg-qc-multi/data/IBD/v2/ibdvars'


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# read data
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# vds_immune = hl.read_matrix_table(vds_immune_file)

# # print('count:')
# # print(vds_immune.count_cols())

# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# # filter variants
# #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ibd_vars = hl.import_locus_intervals(ibdvars_file)
# intervallist = [x.interval for x in ibd_vars.collect()]
# manuelvars = hl.import_locus_intervals(manuelvars_file)
# intervallist = intervallist + [x.interval for x in manuelvars.collect()]

# print('XXX')
# print(len(intervallist))
# print(intervallist[:5])
# print(intervallist[-5:])

# vds_immune = hl.filter_intervals(vds_immune, intervallist, keep=True)

# vds_immune = hl.split_multi_hts(vds_immune.select_entries(vds_immune.GT, vds_immune.AD, vds_immune.DP, vds_immune.GQ, vds_immune.PL))

# vds_immune = vds_immune.repartition(1000)
# vds_immune.write(filtered_vds_immune_file2, overwrite=True)

vds_immune = hl.read_matrix_table(filtered_vds_immune_file2)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# filter samples
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# samples_to_keep = hl.import_table(samples_to_keep_file, no_header=True).key_by('f0')
# vds = vds.filter_cols(hl.is_defined(samples_to_keep[vds.s]), keep=True)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# annotate samples
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

table = hl.import_table(pheno_file, impute=True).key_by('subject_id')
vds_immune = vds_immune.annotate_cols(**table[vds_immune.s])
#vds = vds.filter_cols(vds.diagnosis_class == 'ibd')

# annotate with populations
# table = hl.import_table(predicted_pop_file, impute=True).key_by('Sample')
# vds = vds.annotate_cols(**table[vds.s])

# table = hl.import_table(pca_afr_file, impute=True).key_by('s')
# vds = vds.annotate_cols(**table[vds.s])


# annotate with global PCs
#table = hl.import_table(pc_global_file, impute=True).key_by('s')
#vds = vds.annotate_cols(**table[vds.s])


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# write filtered vds
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

vds = vds_immune

vds = (vds.filter_entries(
     (vds.DP > 400) |
     (vds.DP < 10) |
     (vds.GT.is_hom_ref() & ((vds.AD[0] / vds.DP < 0.9) | (vds.GQ < 20))) |
     (vds.GT.is_hom_var() & ((vds.AD[1] / vds.DP < 0.9) | (vds.PL[0] < 20) )) |
     (vds.GT.is_het() & ( ((vds.AD[0] + vds.AD[1]) / vds.DP < 0.9) |
          (vds.AD[1] / vds.DP < 0.20) |
          (vds.PL[0] < 20)))
     , keep=False))

#hl.export_plink(vds, plink_file, fam_id=vds.s, id=vds.s)


#vds.rows().select('locus', 'alleles').export(ibd_vars_table_file)

#vds = hl.read_matrix_table(filtered_vds_file)

#vds = hl.vep(vds, "/vep/vep-gcloud.properties")

#vds.rows().select('locus', 'alleles', 'vep').flatten().export(logreg_pop_file + '_vep38.tsv')

#vds.cols().select('s', 'sex', 'race_ethnicity', 'diagnosis_specific').flatten().export(samples_file)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# run logreg
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

vdsor = vds

pop = 'AFRICAN_AMERICAN'
pop = 'HISPANIC'
# for pop in ['AFR', 'PUR', 'other']:
if pop == 'AFRICAN_AMERICAN':
	vds = vdsor.filter_cols((vdsor.race_ethnicity == pop))
if pop == 'HISPANIC':
	vds = vdsor.filter_cols((vdsor.race_ethnicity == 'HISPANIC') | (vdsor.race_ethnicity == 'PUERTO_RICAN'))
#vds.cols().flatten().export(samples_file)




for disease in ['meta', 'cd']:
	
	if disease == 'meta':
		vds = hl.logistic_regression(test='wald', y=hl.cond(((vds.diagnosis_specific == 'uc') | (vds.diagnosis_specific == 'cd')), 1, hl.cond(vds.diagnosis_specific == 'control', 0, hl.or_missing(False, 1))), x=vds.GT.n_alt_alleles(), covariates=[vds.sex == 'male'], root='logreg_' + disease)
# , vds.PC1, vds.PC2, vds.PC3, vds.PC4, vds.PC5, vds.PC6, vds.PC7, vds.PC8, vds.PC9, vds.PC10
		vds = vds.annotate_rows(metahomref=hl.agg.count_where(((vds.diagnosis_specific == 'uc') | (vds.diagnosis_specific == 'cd')) & vds.GT.is_hom_ref()),
	                       metahet=hl.agg.count_where(((vds.diagnosis_specific == 'uc') | (vds.diagnosis_specific == 'cd')) & vds.GT.is_het()),
	                       metahomvar=hl.agg.count_where(((vds.diagnosis_specific == 'uc') | (vds.diagnosis_specific == 'cd')) & vds.GT.is_hom_var()),
	                       metamissing=hl.agg.count_where(((vds.diagnosis_specific == 'uc') | (vds.diagnosis_specific == 'cd')) & ~hl.is_defined(vds.GT)))
	if disease == 'cd':
		vds = hl.logistic_regression(test='wald', y=hl.cond(vds.diagnosis_specific == disease, 1, hl.cond(vds.diagnosis_specific == 'control', 0, hl.or_missing(False, 1))), x=vds.GT.n_alt_alleles(), covariates=[vds.sex == 'male'], root='logreg_' + disease)
#, vds.PC1, vds.PC2, vds.PC3, vds.PC4, vds.PC5, vds.PC6, vds.PC7, vds.PC8, vds.PC9, vds.PC10

		vds = vds.annotate_rows(cdhomref=hl.agg.count_where((vds.diagnosis_specific == disease) & vds.GT.is_hom_ref()),
	                       cdhet=hl.agg.count_where((vds.diagnosis_specific == disease) & vds.GT.is_het()),
	                       cdhomvar=hl.agg.count_where((vds.diagnosis_specific == disease) & vds.GT.is_hom_var()),
	                       cdmissing=hl.agg.count_where((vds.diagnosis_specific == disease) & ~hl.is_defined(vds.GT)))



vds = vds.annotate_rows(conthomref=hl.agg.count_where((vds.diagnosis_specific == 'control') & vds.GT.is_hom_ref()),
	                       conthet=hl.agg.count_where((vds.diagnosis_specific == 'control') & vds.GT.is_het()),
	                       conthomvar=hl.agg.count_where((vds.diagnosis_specific == 'control') & vds.GT.is_hom_var()),
	                       contmissing=hl.agg.count_where((vds.diagnosis_specific == 'control') & ~hl.is_defined(vds.GT)))

#vds.rows().select('locus', 'alleles', 'conthomref', 'conthet', 'conthomvar', 'contmissing', 'cdhomref', 'cdhet', 'cdhomvar', 'cdmissing', 'metahomref', 'metahet', 'metahomvar', 'metamissing', 'logreg_cd', 'logreg_meta', 'vep.variant_class').flatten().export(logreg_pop_file + pop + '.tsv')

vds.rows().select('locus', 'alleles', 'conthomref', 'conthet', 'conthomvar', 'contmissing', 'cdhomref', 'cdhet', 'cdhomvar', 'cdmissing', 'metahomref', 'metahet', 'metahomvar', 'metamissing', 'logreg_cd', 'logreg_meta').flatten().export(logreg_pop_file + pop + '.tsv')





# print runtime

stop = timeit.default_timer()
print("runtime: " + str(stop - start) + " seconds")

