import { ApolloClient, InMemoryCache } from '@apollo/client/core'

// Apollo Client configuration
export const apolloClient = new ApolloClient({
  uri: 'http://localhost:5000/graphql',
  cache: new InMemoryCache()
})

// Export Apollo Client for use in components
export default apolloClient
