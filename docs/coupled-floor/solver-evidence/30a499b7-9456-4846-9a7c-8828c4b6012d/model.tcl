wipe
model BasicBuilder -ndm 3 -ndf 6
node 1 0 0 3
node 2 1 0 3
node 3 2 0 3
node 4 3 0 3
node 5 4 0 3
node 6 0 1 3
node 7 1 1 3
node 8 2 1 3
node 9 3 1 3
node 10 4 1 3
node 11 0 2 3
node 12 1 2 3
node 13 2 2 3
node 14 3 2 3
node 15 4 2 3
node 16 0 3 3
node 17 1 3 3
node 18 2 3 3
node 19 3 3 3
node 20 4 3 3
node 21 0 4 3
node 22 1 4 3
node 23 2 4 3
node 24 3 4 3
node 25 4 4 3
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
element elasticBeamColumn 3 3 4 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 3
geomTransf Linear 4 0 0 1
element elasticBeamColumn 4 4 5 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 4
geomTransf Linear 5 0 0 1
element elasticBeamColumn 5 5 10 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 5
geomTransf Linear 6 0 0 1
element elasticBeamColumn 6 10 15 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 6
geomTransf Linear 7 0 0 1
element elasticBeamColumn 7 15 20 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 7
geomTransf Linear 8 0 0 1
element elasticBeamColumn 8 20 25 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 8
geomTransf Linear 9 0 0 1
element elasticBeamColumn 9 25 24 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 9
geomTransf Linear 10 0 0 1
element elasticBeamColumn 10 24 23 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 10
geomTransf Linear 11 0 0 1
element elasticBeamColumn 11 23 22 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 11
geomTransf Linear 12 0 0 1
element elasticBeamColumn 12 22 21 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 12
geomTransf Linear 13 0 0 1
element elasticBeamColumn 13 21 16 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 13
geomTransf Linear 14 0 0 1
element elasticBeamColumn 14 16 11 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 14
geomTransf Linear 15 0 0 1
element elasticBeamColumn 15 11 6 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 15
geomTransf Linear 16 0 0 1
element elasticBeamColumn 16 6 1 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 16
geomTransf Linear 17 0 1 0
element elasticBeamColumn 17 900 1 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 17
geomTransf Linear 18 0 1 0
element elasticBeamColumn 18 901 5 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 18
geomTransf Linear 19 0 1 0
element elasticBeamColumn 19 902 25 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 19
geomTransf Linear 20 0 1 0
element elasticBeamColumn 20 903 21 0.089999999999999997 30000000000 12500000000 0.001 0.00067499999999999993 0.00067499999999999993 20
section ElasticMembranePlateSection 1 30000000000.0 0.2 0.16 0
element ShellMITC4 1000 1 2 7 6 1
element ShellMITC4 1001 2 3 8 7 1
element ShellMITC4 1002 3 4 9 8 1
element ShellMITC4 1003 4 5 10 9 1
element ShellMITC4 1004 6 7 12 11 1
element ShellMITC4 1005 7 8 13 12 1
element ShellMITC4 1006 8 9 14 13 1
element ShellMITC4 1007 9 10 15 14 1
element ShellMITC4 1008 11 12 17 16 1
element ShellMITC4 1009 12 13 18 17 1
element ShellMITC4 1010 13 14 19 18 1
element ShellMITC4 1011 14 15 20 19 1
element ShellMITC4 1012 16 17 22 21 1
element ShellMITC4 1013 17 18 23 22 1
element ShellMITC4 1014 18 19 24 23 1
element ShellMITC4 1015 19 20 25 24 1
timeSeries Linear 1
pattern Plain 1 1 {
load 1 0 0 -1250 0 0 0
load 2 0 0 -2500 0 0 0
load 3 0 0 -2500 0 0 0
load 4 0 0 -2500 0 0 0
load 5 0 0 -1250 0 0 0
load 6 0 0 -2500 0 0 0
load 7 0 0 -5000 0 0 0
load 8 0 0 -5000 0 0 0
load 9 0 0 -5000 0 0 0
load 10 0 0 -2500 0 0 0
load 11 0 0 -2500 0 0 0
load 12 0 0 -5000 0 0 0
load 13 0 0 -5000 0 0 0
load 14 0 0 -5000 0 0 0
load 15 0 0 -2500 0 0 0
load 16 0 0 -2500 0 0 0
load 17 0 0 -5000 0 0 0
load 18 0 0 -5000 0 0 0
load 19 0 0 -5000 0 0 0
load 20 0 0 -2500 0 0 0
load 21 0 0 -1250 0 0 0
load 22 0 0 -2500 0 0 0
load 23 0 0 -2500 0 0 0
load 24 0 0 -2500 0 0 0
load 25 0 0 -1250 0 0 0
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
puts $f "10 [nodeDisp 10]"
puts $f "11 [nodeDisp 11]"
puts $f "12 [nodeDisp 12]"
puts $f "13 [nodeDisp 13]"
puts $f "14 [nodeDisp 14]"
puts $f "15 [nodeDisp 15]"
puts $f "16 [nodeDisp 16]"
puts $f "17 [nodeDisp 17]"
puts $f "18 [nodeDisp 18]"
puts $f "19 [nodeDisp 19]"
puts $f "20 [nodeDisp 20]"
puts $f "21 [nodeDisp 21]"
puts $f "22 [nodeDisp 22]"
puts $f "23 [nodeDisp 23]"
puts $f "24 [nodeDisp 24]"
puts $f "25 [nodeDisp 25]"
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
puts $f "10 [nodeReaction 10]"
puts $f "11 [nodeReaction 11]"
puts $f "12 [nodeReaction 12]"
puts $f "13 [nodeReaction 13]"
puts $f "14 [nodeReaction 14]"
puts $f "15 [nodeReaction 15]"
puts $f "16 [nodeReaction 16]"
puts $f "17 [nodeReaction 17]"
puts $f "18 [nodeReaction 18]"
puts $f "19 [nodeReaction 19]"
puts $f "20 [nodeReaction 20]"
puts $f "21 [nodeReaction 21]"
puts $f "22 [nodeReaction 22]"
puts $f "23 [nodeReaction 23]"
puts $f "24 [nodeReaction 24]"
puts $f "25 [nodeReaction 25]"
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
puts $f "13 [eleResponse 13 localForce]"
puts $f "14 [eleResponse 14 localForce]"
puts $f "15 [eleResponse 15 localForce]"
puts $f "16 [eleResponse 16 localForce]"
puts $f "17 [eleResponse 17 localForce]"
puts $f "18 [eleResponse 18 localForce]"
puts $f "19 [eleResponse 19 localForce]"
puts $f "20 [eleResponse 20 localForce]"
close $f
set f [open shells.tsv w]
puts $f "1000 [eleResponse 1000 forces]"
puts $f "1001 [eleResponse 1001 forces]"
puts $f "1002 [eleResponse 1002 forces]"
puts $f "1003 [eleResponse 1003 forces]"
puts $f "1004 [eleResponse 1004 forces]"
puts $f "1005 [eleResponse 1005 forces]"
puts $f "1006 [eleResponse 1006 forces]"
puts $f "1007 [eleResponse 1007 forces]"
puts $f "1008 [eleResponse 1008 forces]"
puts $f "1009 [eleResponse 1009 forces]"
puts $f "1010 [eleResponse 1010 forces]"
puts $f "1011 [eleResponse 1011 forces]"
puts $f "1012 [eleResponse 1012 forces]"
puts $f "1013 [eleResponse 1013 forces]"
puts $f "1014 [eleResponse 1014 forces]"
puts $f "1015 [eleResponse 1015 forces]"
close $f
exit 0