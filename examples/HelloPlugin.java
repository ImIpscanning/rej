package org.example;
import java.util.List;
public final class HelloPlugin implements Runnable {
    private final String name = "Example";
    public void run() { List<String> xs = List.of("hello", name); System.out.println(xs); }
    public String greet(String who) { return "Hello " + who; }
}
