wipe
model BasicBuilder -ndm 3 -ndf 6
node 1 0 0 3
node 2 2 0 3
node 3 4 0 3
node 4 0 2 3
node 5 2 2 3
node 6 4 2 3
node 7 0 4 3
node 8 2 4 3
node 9 4 4 3
node 900 0 0 0
fix 900 1 1 1 1 1 1
node 901 4 0 0
fix 901 1 1 1 1 1 1
node 902 4 4 0
fix 902 1 1 1 1 1 1
node 903 0 4 0
fix 903 1 1 1 1 1 1
geomTransf Linear 1 0 0 1
element elasticBeamColumn 1 1 2 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 1
geomTransf Linear 2 0 0 1
element elasticBeamColumn 2 2 3 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 2
geomTransf Linear 3 0 0 1
element elasticBeamColumn 3 3 6 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 3
geomTransf Linear 4 0 0 1
element elasticBeamColumn 4 6 9 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 4
geomTransf Linear 5 0 0 1
element elasticBeamColumn 5 9 8 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 5
geomTransf Linear 6 0 0 1
element elasticBeamColumn 6 8 7 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 6
geomTransf Linear 7 0 0 1
element elasticBeamColumn 7 7 4 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 7
geomTransf Linear 8 0 0 1
element elasticBeamColumn 8 4 1 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 8
geomTransf Linear 9 0 1 0
element elasticBeamColumn 9 900 1 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 9
geomTransf Linear 10 0 1 0
element elasticBeamColumn 10 901 3 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 10
geomTransf Linear 11 0 1 0
element elasticBeamColumn 11 902 9 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 11
geomTransf Linear 12 0 1 0
element elasticBeamColumn 12 903 7 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 12
section ElasticMembranePlateSection 1 30000000000.0 0.2 0.16 0
element ShellMITC4 1000 1 2 5 4 1
element ShellMITC4 1001 2 3 6 5 1
element ShellMITC4 1002 4 5 8 7 1
element ShellMITC4 1003 5 6 9 8 1
timeSeries Linear 1
pattern Plain 1 1 {
load 1 0 0 -5000 0 0 0
load 2 0 0 -10000 0 0 0
load 3 0 0 -5000 0 0 0
load 4 0 0 -10000 0 0 0
load 5 0 0 -20000 0 0 0
load 6 0 0 -10000 0 0 0
load 7 0 0 -5000 0 0 0
load 8 0 0 -10000 0 0 0
load 9 0 0 -5000 0 0 0
}
constraints Plain
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
puts $f "5 [nodeDisp 5]"
puts $f "6 [nodeDisp 6]"
puts $f "7 [nodeDisp 7]"
puts $f "8 [nodeDisp 8]"
puts $f "9 [nodeDisp 9]"
puts $f "900 [nodeDisp 900]"
puts $f "901 [nodeDisp 901]"
puts $f "902 [nodeDisp 902]"
puts $f "903 [nodeDisp 903]"
close $f
set f [open reactions.tsv w]
puts $f "1 [nodeReaction 1]"
puts $f "2 [nodeReaction 2]"
puts $f "3 [nodeReaction 3]"
puts $f "4 [nodeReaction 4]"
puts $f "5 [nodeReaction 5]"
puts $f "6 [nodeReaction 6]"
puts $f "7 [nodeReaction 7]"
puts $f "8 [nodeReaction 8]"
puts $f "9 [nodeReaction 9]"
puts $f "900 [nodeReaction 900]"
puts $f "901 [nodeReaction 901]"
puts $f "902 [nodeReaction 902]"
puts $f "903 [nodeReaction 903]"
close $f
set f [open beams.tsv w]
puts $f "1 [eleResponse 1 localForce]"
puts $f "2 [eleResponse 2 localForce]"
puts $f "3 [eleResponse 3 localForce]"
puts $f "4 [eleResponse 4 localForce]"
puts $f "5 [eleResponse 5 localForce]"
puts $f "6 [eleResponse 6 localForce]"
puts $f "7 [eleResponse 7 localForce]"
puts $f "8 [eleResponse 8 localForce]"
puts $f "9 [eleResponse 9 localForce]"
puts $f "10 [eleResponse 10 localForce]"
puts $f "11 [eleResponse 11 localForce]"
puts $f "12 [eleResponse 12 localForce]"
close $f
set f [open shells.tsv w]
puts $f "1000 [eleResponse 1000 forces]"
puts $f "1001 [eleResponse 1001 forces]"
puts $f "1002 [eleResponse 1002 forces]"
puts $f "1003 [eleResponse 1003 forces]"
close $f
exit 0