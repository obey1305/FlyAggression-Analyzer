% Diagnostic: native200FPS tracking with the full-recording background and body calibration.
% Standalone2-second automatic calibration failed; this is not full200FPS validation.
restoredefaultpath;project=fileparts(fileparts(fileparts(mfilename('fullpath'))));out=fileparts(project);
addpath(fullfile(out,'raw-video-integration','FlyTracker'));modpath;addpath(fullfile(out,'raw-video-integration','auto-calibration'));
load(fullfile(project,'data','v23-input','movie5-rectangular-calibration.mat'),'calib');
bgfile=fullfile(project,'data','v23-tracking','movie5-analysis30','movie5-analysis30-bg.mat');load(bgfile,'bg');
video=fullfile(project,'data','v23-input','native200-probe.avi');v=VideoReader(video);assert(v.FrameRate==200);calib.FPS=200;
p=infer_parameters(calib,bg,im2double(read(v,200)));
for f={'vel_thresh','choose_orientations_weight_theta','vel_fil'},calib.params.(f{1})=p.(f{1});end
options=tracker_default_options();options.isdisplay=false;options.num_cores=1;options.num_chunks=1;options.do_use_scratch_folder_for_intermediates=false;
d=fullfile(project,'data','v23-native-probe-full-background');if ~isfolder(d),mkdir(d);end
trackfile=fullfile(d,'native200-track.mat');core_core_tracker(trackfile,bgfile,fullfile(d,'native200-seg.mat'),video,options,calib);
load(trackfile,'trk');feat=feat_compute(trk,calib,true);save(fullfile(d,'native200-feat.mat'),'feat','-v7.3');
s=struct('status','short native tracking completed with full-recording background/body calibration','native_fps',200,'track_shape',size(trk.data),'feature_shape',size(feat.data),'velocity_kernel_samples',numel(calib.params.vel_fil),'full_native_recording_tracked',false,'standalone_short_calibration_passed',false,'source_clip_offset_seconds',640,'aggression_classifier_used',false);
fid=fopen(fullfile(project,'reports','v23-days1-4','native-probe-result.json'),'w');fwrite(fid,jsonencode(s));fclose(fid);
