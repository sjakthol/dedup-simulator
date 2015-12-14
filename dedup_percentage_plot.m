% function [] = dedup_percentage_plot(directory, glob)
%   files = dir(fullfile(directory, glob));
%   names = { files(~[files.isdir]).name };
%   for f = names
%       file = char(fullfile(directory, f));
%       data = csvread(file);
%       ys = data(:, 2);
%       xs = data(:, 1);
%       percentages = 1 - ys ./ xs;
%       %xsx = 1:step:length(data)*step;
%       %[rows, cols] = size(data);
%       %if rows > cols
%       %    percentages = 1 - data' ./ xsx;
%       %else
%       %    percentages = 1 - data ./ xsx;
%       %end
%       plot(xs, percentages);
%   end
% end

function [] = scatter_plot(data, n)
  idxs = repelem(n, length(data));
  scatter(idxs, data)
end