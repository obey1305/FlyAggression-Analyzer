% Compare representative decoded RGB frames using MATLAB's actual tracker reader.
restoredefaultpath;project=fileparts(fileparts(fileparts(mfilename('fullpath'))));
a=VideoReader(fullfile(fileparts(project),'new-training-data','BoyMeetsBoy','downloads','movie5.avi'));
b=VideoReader(fullfile(project,'data','v23-input','movie5-analysis30.mp4'));
map=readtable(fullfile(project,'reports','v23-days1-4','frame-time-map.csv'));
indices=unique(round(linspace(1,height(map),9)));rows=[];
for k=indices
 src=map.source_frame(k);x=read(a,src);y=read(b,k);d=abs(double(x)-double(y));
 rows=[rows;struct('analysis_frame',k,'source_frame',src,'max_rgb_difference',max(d(:)),'mean_rgb_difference',mean(d(:)),'fraction_nonidentical_channels',mean(d(:)>0))];
 if k==indices(1)||k==indices(5)||k==indices(end)
  imwrite(y,fullfile(project,'reports','v23-days1-4',sprintf('analysis-frame-%06d.png',k)));
 end
end
fid=fopen(fullfile(project,'reports','v23-days1-4','representative-reader-check.json'),'w');fwrite(fid,jsonencode(rows));fclose(fid);
