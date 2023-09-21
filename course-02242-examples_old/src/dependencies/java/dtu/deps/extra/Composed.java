package dtu.deps.extra;

public class Composed {
    private Pregnant person = new Pregnant();
    public First first;

    public Composed(short month){
        First f = new First();
        this.first = f;
        this.person.month = month;
    }

    public void proxySetMethod(){
        short proxy = 12;
        this.person.month = replaceMonth(proxy);
    }

    public short replaceMonth(short newMonth) {
        return newMonth;
    }
}
