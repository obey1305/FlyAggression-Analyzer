% Independent official MATLAB augmentation comparison for the prepared cohort.
root=fileparts(fileparts(mfilename('fullpath')));
restoredefaultpath;addpath(fullfile(fileparts(root),'raw-video-integration','FlyTracker'));modpath;
all_names=jsondecode(fileread(fullfile(root,'config','feature-columns.json')));names=all_names(1:12)';
for index=1:5
 rec=sprintf('movie%d',index);folder=fullfile(root,'data',rec);
 f=load(fullfile(folder,'raw-features.mat'));[found,indices]=ismember(names,f.feat.names);assert(all(found));
 expected=feat_augment_data(f.feat.data(:,:,indices),names);
 assert(isequal(size(expected),[2,54000,36]));
 save(fullfile(folder,'matlab-augmentation-reference.mat'),'expected','-v7');
 fprintf('%s AUGMENTATION_REFERENCE_READY\n',rec);
end
