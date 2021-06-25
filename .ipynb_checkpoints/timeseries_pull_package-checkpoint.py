"""
# Timeseries Pull with FSL Package

"""

## imports
from IPython.core import display as ICD

import os, glob
import pandas as pd
import nipype.interfaces.fsl as fsl
import multiprocessing as mp
import time



class FMRITimeseries:
    """
    ## ROI Timeseries Pull Helper Functions
    Definitions of the timeseries programs common functions.
    """
    def __init__(self, func_folders):
        self.func_folders = func_folders
        self.data_dict = {}


    # Helper Functions


    ## build_chunklist()
    def build_chunklist(self, subject_ids=[],chunksize=2):
        # set dataset list l
        if not subject_ids:
            l=self.func_folders
        else:
            l=subject_ids

        n=chunksize
        # break dataset into chunksize n
        """if len(l) > 200:
            n=len(l)//100 # set chunksize
        elif len(l) > 50:
            n=len(l)//20 # set chunksize
        elif len(l) > 25:
            n=len(l)//10# set chunksize
        else:
            n=len(l)//5 # set chunksize
        print('[INFO] CHUNK SIZE: %s'%n)"""

        # grab concatenated (fslmerge) data
        chunk_list=[l[i:i+n] for i in range(0, len(l), n)]
        print('[INFO] CHUNK LIST SIZE: %s'%(len(chunk_list)))

        return chunk_list;

    ## make the dictionary with subject ids and task (resting or functional expected)
    def setup_dictionary(self, filtered_func=False, verbose=False):
        # setup a dictionary
        data_dict={}
        print("[INFO] building dictionary....")
        for folder in self.func_folders:
            #print(func_file.split("/")[-1])
            subj_id = folder.split("/")[-2]
            task_id = folder.split("/")[-1]

            # task string edits
            if ".feat" in task_id:
                task_id=task_id.replace('.feat', '')
            if verbose==True: print('[INFO] subject: %s \t task: %s'%(subj_id, task_id))
            if subj_id not in data_dict:
                data_dict[subj_id]={}
            if task_id not in data_dict[subj_id]:
                data_dict[subj_id][task_id]={}

            if filtered_func == True:
                flt_func_file=os.path.join(folder, 'filtered_func_data.nii.gz')
                data_dict[subj_id][task_id]['FILTER_FUNC']=flt_func_file

        self.data_dict=data_dict
        return data_dict;


    #########################################
    ## transform nifits -- with FSL flirt
    def fsl_flirt(self,subject,target_task, verbose=False):
        # set references file paths
        reference_nifti= '/projects/niblab/parcellations/chocolate_decoding_rois/mni2ace.nii.gz'
        reference_matrix= '/projects/niblab/parcellations/chocolate_decoding_rois/mni2ace.mat'
        out_folder=os.path.join('/projects/niblab/experiments/project_milkshake/data/timeseries/folder1')

        # loop through tasks and select given task
        for subject_task in data_dict[subject]:

            # get target task
            if subject_task in target_task:

                if verbose==True: print('[INFO] Applying a transformation to {} {} file with FSL flirt.'.format(subject,target_task))

                img=data_dict[subject][target_task]['FILTER_FUNC']
                #func_imgs = os.path.join(os.path.join())
                #print('[INFO] func img found: %s'%func_img)

                ## setup command input variables
                #filename=
                outfile='{}_{}_3mm.nii.gz'.format(subject, target_task)
                outfile=os.path.join(out_folder,outfile)
                #print('[INFO] out file: {}'.format(out_file))

                # intiialize objects
                applyxfm = fsl.preprocess.ApplyXFM()

                # set command variables
                applyxfm.inputs.in_file=img # input img filename
                applyxfm.inputs.reference=reference_nifti #input reference img filename
                applyxfm.inputs.in_matrix_file=reference_matrix # input reference matrix
                applyxfm.inputs.out_file=outfile# output img filename
                # apply transformation supplied by the matrix file
                applyxfm.inputs.apply_xfm = True
                if verbose==True: print('[INFO] IMAGE %s FILE: \n%s'%(out_folder, applyxfm.inputs)) # check command
                ## run FSL Flirt command
                result = applyxfm.run()
                # add outfile to dictionary



            else:
                #print('[INFO] ERROR: target task {} not found in subject {}'.format(target_task, subject))
                pass

    #########################################
    # fslmaths command to threshold --use binary option for transforming masks
    def fsl_fslmaths(self,subject, target_task, data_path, verbose=False, th=0.9):

        # loop through tasks and select given task
        for subject_task in data_dict[subject]:

            # get target task
            if subject_task in target_task:
                # get input file
                in_file=os.path.join(data_path, "{}_{}_3mm.nii.gz".format(subject, target_task))
                outfile=os.path.join(data_path, "{}_{}.nii.gz".format(subject, target_task))
                #print(in_file,outfile)


                # intialize command object and set variables
                fslmaths = fsl.maths.Threshold()
                fslmaths.inputs.in_file = in_file
                fslmaths.inputs.out_file = outfile
                fslmaths.inputs.thresh = th
                # run command
                result = fslmaths.run()
                data_dict[subject][subject_task]['func_3mm']=outfile

    # fslmeants command
    def fsl_fslmeants(self, file, out_dir, bb300_path='/projects/niblab/parcellations/bigbrain300', roi_df='/projects/niblab/parcellations/bigbrain300/renaming.csv', verbose=True, run_process=False):

        input_nifti=file

        # load asymmetrical nifti reference ROI file
        asym_niftis=glob.glob("/projects/niblab/parcellations/bigbrain300/MNI152Asymmetrical_3mm/*.nii.gz")

        # loop through roi reference list
        for ref_nifti in sorted(asym_niftis):
            #print('[INFO] reference roi: %s'%ref_nifti)
            roi = ref_nifti.split('/')[-1].split(".")[0]
            outname=input_nifti.split("/")[-1].replace(input_nifti.split("/")[-1].split(".")[0], input_nifti.split("/")[-1].split(".")[0]+"_"+roi)
            if verbose==True: print('[INFO] building outfile: %s'%(outname))
            output_file = os.path.join(out_dir, outname)

            #initialize object
            fslmeants = fsl.utils.ImageMeants()
            fslmeants.inputs.in_file = input_nifti
            fslmeants.inputs.out_file = output_file
            fslmeants.inputs.mask = ref_nifti
            if verbose==True: print("[INFO] input: {} \noutput: {} \nref mask: {}".format(fslmeants.inputs.in_file, fslmeants.inputs.out_file, fslmeants.inputs.mask))
            # run command
            if run_process==True: result=fslmeants.run()






#---------------------#

# *Main Program*
#########################################

multi_task=False
single_task=True

#########################################
# **Helper Functions** ##

# loops through subject ids and performs a task
def subject_loop(subject, process='fslmaths'):
    if single_task == True:
        task='mk1'
        if process=="flirt":
            obj1.fsl_flirt(subject, task)
        elif process=="fslmaths":
            obj1.fsl_fslmaths(subject, target_task=task,
                              data_path= '/projects/niblab/experiments/project_milkshake/data/timeseries/funcs_3mm')

    if multi_task == True:
        task_list=['mk1', 'mk2', 'mk3', 'mk4', 'mk5']

        for task in task_list:
            task=task
            if process=="flirt":
                obj1.fsl_flirt(subject, task)
            elif process=="fslmaths":
                obj1.fsl_fslmaths(subject, target_task=task,
                              data_path= '/projects/niblab/experiments/project_milkshake/data/timeseries/funcs_3mm')
