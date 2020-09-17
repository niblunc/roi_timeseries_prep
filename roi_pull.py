import os, glob
import sys
import multiprocessing as mp
import time

sys.path.append('/projects/niblab/jupyter_notebooks')
import timeseries_pull as tp


print("[INFO] PROGRAM STARTING....")
# path that holds the subjects
data_path='/projects/niblab/experiments/project_milkshake/derivatives'

# get subject task functional images (niftis)
# -- note: this code grabs functional images,  usually resting or functional-tasks.
# This code may be unique, may be more efficient way to grab user code.
func_folders=glob.glob(os.path.join(data_path,'sub-*/*'))
# sort images
func_folders.sort()
# initialize fmri timeseries class object --inherites functional image list
obj1 = tp.FMRITimeseries(func_folders)

## Step 3: Pull individual ROI timeseries from each subject, by task/condition
out_dir = os.path.join('/projects/niblab/experiments/project_milkshake/data/timeseries/bigbrain300/rois')
target_task = "mk1"
fslmeants_start_time = time.time()
task_list = ['mk1', 'mk2', 'mk3', 'mk4', 'mk5']

data_dict=obj1.setup_dictionary(filtered_func=True)
# set a list of subject ids from the dictionary 1st level keys
subject_ids=list(data_dict.keys())
subject_ids.sort()
subject_ct=len(subject_ids) # get count of subject dataset
print("[INFO] Dictionary made, {} keys".format(len(data_dict.keys())))
#print("[INFO] Keys: {}".format(subject_ids))


# build chunklist
chunk_list=obj1.build_chunklist(subject_ids=subject_ids,chunksize=4)



def loop_one(subject):
    # print(subject)
    niftis = glob.glob(
        "/projects/niblab/experiments/project_milkshake/data/timeseries/funcs_3mm/{}*.nii.gz".format(subject))

    for nifti in niftis:
        obj1.fsl_fslmeants(nifti, out_dir, verbose=False, run_process=True)

for chunks in chunk_list[:1]:
    with mp.Pool(4) as p:
        p.map(loop_one, chunks)
        p.close()

fslmeants_process_time = time.time() - fslmeants_start_time
print("[INFO] process complete in --- %s seconds ---" % fslmeants_process_time)







