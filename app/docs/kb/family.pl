male(ali).
male(asim).
male(john).
male(mike).
male(bob).

female(sara).
female(asia).
female(sehar).
female(lisa).
female(emily).
female(susan).

parent(ali, sehar).
parent(asia, sehar).
parent(asim, ali).
parent(sara, asia).
parent(john, lisa).
parent(john, mike).
parent(lisa, emily).
parent(bob, susan).

father(Father, Child):- male(Father), parent(Father, Child).
mother(Mother, Child):- female(Mother), parent(Mother, Child).

dada(Dada, Pota):- male(Dada), male(Father), parent(Dada, Father), parent(Father, Pota).
dadi(Dadi, Pota):- female(Dadi), male(Father), parent(Dadi, Father), parent(Father, Pota).

nana(Nana, Nawasa):- male(Nana), female(Mother), parent(Nana, Mother), parent(Mother, Nawasa).
nani(Nani, Pota):- female(Nani), female(Mother), parent(Nani, Mother), parent(Mother, Pota).