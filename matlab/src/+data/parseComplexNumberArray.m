function out = parseComplexNumberArray(data)
% Parse an array of complex numbers into a data matrix. Assume each field
% in the struct is a column, and assume they are all the same length.

out = data.real_samples + data.imag_samples*1i;

end