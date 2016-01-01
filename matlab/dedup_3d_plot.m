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

function [] = dedup_3d_plot(x, y, z)
  % x is a vector containing the rate limits
  % y is a vector containing the maximum thresholds
  % z is a vector containing the deduplication percentages

  [xi, yi] = meshgrid(min(x):10:max(x), min(y):1:max(y));
  zi = griddata(x, y, z, xi, yi);
  surf(xi, yi, zi);
end
