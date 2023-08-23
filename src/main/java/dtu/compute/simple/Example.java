package dtu.compute.simple;

import dtu.compute.util.Utils;

// import some.other.Class;

// Known Dependencies
// -> dtu.compute.simple.Other
// -> dtu.compute.util.Utils
// -> java.lang.String

/**
 * This is an example class that contains dependencies.
 *
 * Known dependencies:
 */
public class Example {
    Other other = new Other();

    public static void main(String[] args) {
        Utils.printHello();
    }

}
