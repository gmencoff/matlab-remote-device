function out = parseComplexNumberArray(data)
% Parse an array of complex numbers into a data matrix. Assume each field
% in the struct is a column, and assume they are all the same length.

fields = fieldnames(data.real_samples);
ncols = length(fields);
nrows = length(data.real_samples.(fields{1}));
out = zeros(nrows,ncols);
for i = 1:ncols
    out(:,i) = data.real_samples.(fields{i}) + data.imag_samples.(fields{i})*1i;
end

end