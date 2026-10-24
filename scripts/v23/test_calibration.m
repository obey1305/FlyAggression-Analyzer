restoredefaultpath;project=fileparts(fileparts(fileparts(mfilename('fullpath'))));addpath(fullfile(project,'scripts','v23'));
video=fullfile(project,'data','v23-input','movie5-analysis30.mp4');destination=fullfile(project,'data','v23-input','must-not-exist.mat');assert(~isfile(destination));
cases={[0 10 620 479],12;[20 10 641 479],12;[620 10 20 479],12;[20.5 10 620 479],12;[20 10 620 479],-1;[1 1 640 480],0};
for i=1:size(cases,1)
 rejected=false;try,rectangular_calibration(video,destination,12,cases{i,1},cases{i,2});catch,rejected=true;end
 assert(rejected,'Invalid geometry was accepted');assert(~isfile(destination),'Invalid geometry created calibration');
end
load(fullfile(project,'data','v23-input','movie5-rectangular-calibration.mat'),'calib');assert(calib.FPS==30&&calib.PPM==12);assert(isequal(size(calib.mask),[480 640]));assert(isequal(calib.rois,[1 1 480 640]));assert(all(calib.mask(:,8:632),'all'));assert(~any(calib.mask(:,[1:7 633:640]),'all'));assert(numel(calib.params.vel_fil)==3);
fid=fopen(fullfile(project,'reports','v23-days1-4','calibration-tests.json'),'w');fwrite(fid,jsonencode(struct('status','PASS','invalid_geometries_rejected',size(cases,1),'positive_mask_and_roi_verified',true,'velocity_kernel_samples',numel(calib.params.vel_fil))));fclose(fid);
