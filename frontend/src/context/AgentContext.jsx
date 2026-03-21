import { createContext, useContext, useReducer, useCallback } from "react";

const INIT = {
  form:          { repo: "", team: "", leader: "" },
  running:       false,
  elapsed:       0,
  logs:          [],
  failures:      [],
  fixes:         [],
  ciRuns:        [],
  result:        null,
  activeTab:     "terminal",
  activeFilter:  "ALL",
  maxIterations: 5,
};

function reducer(state, { type, payload }) {
  switch (type) {
    case "SET_FORM":     return { ...state, form: { ...state.form, ...payload } };
    case "START":        return { ...state, running: true, elapsed: 0, logs: [], failures: [], fixes: [], ciRuns: [], result: null, activeTab: "terminal", activeFilter: "ALL" };
    case "TICK":         return { ...state, elapsed: state.elapsed + 1 };
    case "ADD_LOG":      return { ...state, logs: [...state.logs, payload] };
    case "ADD_FAILURE":  return { ...state, failures: [...state.failures, payload] };
    case "SET_FIXES":    return { ...state, fixes: payload };
    case "ADD_CIRUN":    return { ...state, ciRuns: [...state.ciRuns, payload] };
    case "COMPLETE":     return { ...state, running: false, result: payload };
    case "SET_TAB":      return { ...state, activeTab: payload };
    case "SET_FILTER":   return { ...state, activeFilter: payload };
    case "SET_MAX_ITER": return { ...state, maxIterations: payload };
    default:             return state;
  }
}

const Ctx = createContext(null);

export function AgentProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, INIT);
  const actions = {
    setForm:      useCallback(p  => dispatch({ type: "SET_FORM",     payload: p  }), []),
    start:        useCallback(()  => dispatch({ type: "START",        payload: null }), []),
    tick:         useCallback(()  => dispatch({ type: "TICK",         payload: null }), []),
    addLog:       useCallback(p  => dispatch({ type: "ADD_LOG",      payload: p  }), []),
    addFailure:   useCallback(p  => dispatch({ type: "ADD_FAILURE",  payload: p  }), []),
    setFixes:     useCallback(p  => dispatch({ type: "SET_FIXES",    payload: p  }), []),
    addCiRun:     useCallback(p  => dispatch({ type: "ADD_CIRUN",    payload: p  }), []),
    complete:     useCallback(p  => dispatch({ type: "COMPLETE",     payload: p  }), []),
    setTab:       useCallback(p  => dispatch({ type: "SET_TAB",      payload: p  }), []),
    setFilter:    useCallback(p  => dispatch({ type: "SET_FILTER",   payload: p  }), []),
    setMaxIter:   useCallback(p  => dispatch({ type: "SET_MAX_ITER", payload: p  }), []),
  };
  return <Ctx.Provider value={{ state, actions }}>{children}</Ctx.Provider>;
}

export function useAgent() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAgent must be used inside AgentProvider");
  return ctx;
}
