% Copyright 2015 Secure Systems Group, Aalto University https://se-sy.org/.
%
% Licensed under the Apache License, Version 2.0 (the "License");
% you may not use this file except in compliance with the License.
% You may obtain a copy of the License at
%
%     http://www.apache.org/licenses/LICENSE-2.0
%
% Unless required by applicable law or agreed to in writing, software
% distributed under the License is distributed on an "AS IS" BASIS,
% WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
% See the License for the specific language governing permissions and
% limitations under the License.

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