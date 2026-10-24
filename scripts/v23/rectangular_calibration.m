function rectangular_calibration(video,destination,ppm,bounds,padding)
% Version2.3: configurable rectangular mask, existing FlyTracker detector calibration.
% Pixel bounds are inclusive[x1 y1 x2 y2]. PPM evidence recorded separately.
root=fileparts(fileparts(fileparts(fileparts(mfilename('fullpath')))));
addpath(fullfile(root,'raw-video-integration','FlyTracker'));modpath;
addpath(fullfile(root,'raw-video-integration','auto-calibration'));
v=VideoReader(video);assert(v.FrameRate==30||v.FrameRate==200,'Unsupported analysis FPS');assert(isfinite(ppm)&&ppm>0,'Invalid scale');
validateattributes(bounds,{'numeric'},{'vector','numel',4,'finite','integer'});validateattributes(padding,{'numeric'},{'scalar','finite','integer','nonnegative'});
assert(1<=bounds(1)&&bounds(1)<bounds(3)&&bounds(3)<=v.Width&&1<=bounds(2)&&bounds(2)<bounds(4)&&bounds(4)<=v.Height,'Invalid rectangle bounds');
assert(~isfile(destination),'Existing calibration must be preserved; choose a new destination');
x1=max(1,bounds(1)-padding);y1=max(1,bounds(2)-padding);x2=min(v.Width,bounds(3)+padding);y2=min(v.Height,bounds(4)+padding);assert(x1<x2 && y1<y2);
mask=false(v.Height,v.Width);mask(y1:y2,x1:x2)=true;assert(any(~mask(:)),'Mask needs outside pixels for finite wall distance');
options=tracker_default_options();options.isdisplay=false;vinfo=video_open(video,1);bg=calib_bg_estimate(vinfo,ppm,[],options);img=video_read_frame(vinfo,floor(vinfo.n_frames/2));
calib=struct('auto_detect',0,'n_chambers',1,'n_rows',1,'n_cols',1,'roi_type',1,'FPS',v.FrameRate,'PPM',ppm,'centroids',[(y1+y2)/2 (x1+x2)/2],'r',[],'w',x2-x1+1,'h',y2-y1+1,'n_flies',2,'magnet',0,'dead_female',0,'valid_chambers',1,'mask',mask,'full_mask',mask,'rois',[1 1 v.Height v.Width]);
calib.masks={mask};calib.params=infer_parameters(calib,bg,img);calib=refine_parameters(calib,bg,vinfo,options);
calib.v23=struct('geometry','manual padded rectangle','bounds',bounds,'padding_pixels',padding,'physical_scale_status','published nominal12pixels/mm; no per-record physical measurement certificate','source_fps',v.FrameRate);
save(destination,'calib','-v7.3');
preview=im2uint8(bg.bg_mean);if size(preview,3)==1,preview=repmat(preview,[1 1 3]);end
preview([y1 y2],x1:x2,1)=255;preview(y1:y2,[x1 x2],1)=255;imwrite(preview,[destination '.png']);
report=struct('fps',v.FrameRate,'frames',vinfo.n_frames,'width',v.Width,'height',v.Height,'pixels_per_mm',ppm,'nominal_geometry_bounds',bounds,'padding_pixels',padding,'tracking_mask_bounds',[x1 y1 x2 y2],'body_mean_area',calib.params.mean_area,'body_mean_major_axis',calib.params.mean_major_axis,'contrast_threshold',calib.params.contrast_th,'geometry','rectangle','physically_measured',false);
fid=fopen([destination '.json'],'w');fwrite(fid,jsonencode(report));fclose(fid);
end
