% Reproducible offline import/tracking only. No classifier invocation.
restoredefaultpath;
project=fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(project,'scripts','v23'));
video=fullfile(project,'data','v23-input','movie5-analysis30.mp4');
calibration=fullfile(project,'data','v23-input','movie5-rectangular-calibration.mat');
assert(isfile(fullfile(project,'reports','v23-days1-4','conversion-verification.json')),'Verify conversion before tracking');
rectangular_calibration(video,calibration,12,[20 10 620 479],12);
videos=struct('dir_in',fullfile(project,'data','v23-input'),'dir_out',fullfile(project,'data','v23-tracking'),'filter','movie5-analysis30.mp4');
options=struct('num_cores',4,'num_chunks',16,'isdisplay',false,'n_flies',2,'save_JAABA',false,'save_xls',false,'save_seg',false,'do_delete_intermediate_results',true,'do_use_scratch_folder_for_intermediates',false,'do_compute_relative_features',true);
fprintf('Pinned tracker: %s\n',which('tracker'));fprintf('Pinned infer_parameters: %s\n',which('infer_parameters'));
tracker(videos,options,calibration);
