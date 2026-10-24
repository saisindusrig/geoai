wipe
model BasicBuilder -ndm 3 -ndf 6
node 1 0 0 3
fix 1 0 0 1 1 1 0
uniaxialMaterial Elastic 1 1000000
uniaxialMaterial Elastic 2 2000000
node 2 2 0 3
node 12 2 0 3
fix 2 0 0 1 1 1 0
fix 12 1 1 1 1 1 1
element zeroLength 2 12 2 -mat 1 2 -dir 1 2
node 3 -2 0 3
node 13 -2 0 3
fix 3 0 0 1 1 1 0
fix 13 1 1 1 1 1 1
element zeroLength 3 13 3 -mat 1 2 -dir 1 2
node 4 0 2 3
node 14 0 2 3
fix 4 0 0 1 1 1 0
fix 14 1 1 1 1 1 1
element zeroLength 4 14 4 -mat 1 2 -dir 1 2
rigidDiaphragm 3 1 2 3 4
timeSeries Linear 1
pattern Plain 1 1 {load 1 1000 500 0 0 0 300}
constraints Transformation
numberer RCM
system BandGeneral
algorithm Linear
integrator LoadControl 1
analysis Static
if {[analyze 1] != 0} {exit 2}
reactions
set f [open nodes.tsv w]
puts $f "1 [nodeDisp 1]"
puts $f "2 [nodeDisp 2]"
puts $f "3 [nodeDisp 3]"
puts $f "4 [nodeDisp 4]"
close $f
exit 0