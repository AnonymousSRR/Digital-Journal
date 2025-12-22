# Guidelines

This document provides guidelines for developing a Java SpringBoot project.
It includes coding standards, Spring Boot best practices and testing recommendations to follow.

### Prerequisites
- Java 17 or later

### Project Structure

Follow **package-by-feature/module** and in each module **package-by-layer** code organization style:

```shell
project-root/
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/mycompany/projectname/
│   │   │       ├── config/
│   │   │       ├── module1/
│   │   │       │     ├── api/
│   │   │       │     │   ├── controllers/
│   │   │       │     │   └── dtos/
│   │   │       │     ├── config/
│   │   │       │     ├── domain/
│   │   │       │     │   ├── entities/
│   │   │       │     │   ├── exceptions/
│   │   │       │     │   ├── mappers/
│   │   │       │     │   ├── models/
│   │   │       │     │   ├── repositories/
│   │   │       │     │   └── services/
│   │   │       │     ├── jobs/
│   │   │       │     ├── eventhandlers/
│   │   └── resources/
│   │       └── application.properties
│   └── test/
│   │   └── java/
│   │   │   └── com/mycompany/projectname/
│   │   │       ├── module1/
│   │   │       │     ├── api/
│   │   │       │     │   ├── controllers/
│   │   │       │     ├── domain/
│   │   │       │     │   └── services/
└── README.md
```

1. **Web Layer** (`com.companyname.projectname.module.api`):
    - Controllers handle HTTP requests and responses
    - DTOs for request/response data
    - Global exception handling

2. **Service Layer** (`com.companyname.projectname.module.domain.services`):
    - Business logic implementation
    - Transaction management

3. **Repository Layer** (`com.companyname.projectname.module.domain.repositories`):
    - Spring Data JPA repositories
    - Database access

4. **Entity Layer** (`com.companyname.projectname.module.domain.entities`):
    - JPA entities representing database tables

5. **Model Layer** (`com.companyname.projectname.module.domain.models`):
    - DTOs for domain objects
    - Command objects for operations

6. **Mapper Layer** (`com.companyname.projectname.module.domain.mappers`):
    - Converters from DTOs to JPA entities and vice-versa

7. **Exceptions** (`com.companyname.projectname.module.domain.exceptions`):
    - Custom exceptions

8. **Config** (`com.companyname.projectname.module.config`):
    - Spring Boot configuration classes such as WebMvcConfig, WebSecurityConfig, etc.

---

## JAVA CODING GUIDELINES (MANDATORY)

### Class Design
- **Should be small**: If large, split into smaller classes
    - Small number of fields: maximum: 7, split where needed
    - Small number of public methods: maximum: ~3-5
- **Single clear purpose**, aligned with **Domain-Driven Design (DDD)**
- **Encapsulation** - Hide internal structure.
- **Domain-focused naming** (e.g., `PolicyRenewalService`, not `HelperUtil`)
    - Avoid vague classes like `Manager`, `Processor`, `Handler` unless domain-specific
    - Use **domain/ubiquitous language** for classes, methods, and variables
- **Avoid "God objects"** each class has a focused role
- Base class should know nothing about their derivatives.
- Prefer dedicated value objects to a primitive type.
    - Keep DTOs dumb, mapping centralised.
    - Logic belongs in services or domain entities carefully.
    - Centralize mapping in Mapper classes (e.g., `TemplateMapper`)
    - Consider entity instance methods for self-contained transformations that do not depend on external DTOs.
- Prefer non-static methods to static methods.
- **Prefer immutability** where practical
- Prefer polymorphism to if/else or switch/case
- Favour **Composition over inheritance** - prefer small collaborating components
- Follow **Law of Demeter** - A class should know only its direct dependencies.
- **Avoid util classes** keep behavior logic close to the data it acts on
- Pay attention to using the right data structures
- Use appropriate access-specifiers

### Method Design
- Small methods - Ideal length: ~3 lines, rarely more than 5
- Avoid one-line methods unless they are being used
- Each method represents a single **atomic step of logic**
- Method names should describe *what* they do (not *how*)
- Have no side effects
- **Use early returns** use guard clauses, expensive operations later
- Avoid nested ifs/loops
- **Don’t use flag arguments**. Split method into several independent methods that can be called from the client without the flag.
- Split Validations into dedicated private methods (e.g. `validateSignatureConfiguration()`)
- Better to have many functions than to pass some code into a function to select a behavior
- Extract complex predicate logic into well-named boolean methods. e.g. `isTemplateDeletionNeeded()`

### Naming Guidelines
- Choose descriptive and unambiguous names.
    - Methods: verbs or verb phrases
    - Classes/DTOs: nouns
    - Variables: clear names (avoid single letters except in trivial loops)
- Prefer smaller names, but also feel free to go with longer names if it expresses intent better
- Make meaningful distinctions
- Use pronounceable names.
- Use searchable names.
- Avoid encodings. Don’t append prefixes or type information.

### SourceCode Formatting Etiquette
- Separate concepts vertically.
- Related code should appear vertically dense.
- Declare variables close to their usage.
- Dependent functions should be close
- Similar functions should be close.
- Keep private methods to be grouped at the bottom of the class for scanability
- Place functions in the downward direction.
- Keep lines short.
- Don’t use horizontal alignment.
- Use white space to associate related things and disassociate weakly related.
- Don’t break indentation.

### API Design
- Use domain-driven design (DDD) for API design
- Follow RESTful conventions
- Consistent resource naming and parameters
- REST endpoints to use nouns rather than verbs (recommended pattern: `noun/sub-resource`)
- Use plural noun resources: `/v1/templates`, add sub-resources `/defaults`, `/bulk-delete`.
- Accept filtering & expansion parameters to reduce endpoint proliferation.
- Ensure tenant/market context is always explicit on requests affecting tenant data. No duplicate/overlapping endpoints.
- Avoid wrapper DTO if single collection or simple scalar is returned.

### Collections and Stream Usage
- Minimize passes; combine filtering & mapping where readable.
- Use typed collections and avoid duplicate traversals while streaming
- Use `Stream.toList()` (immutability accepted) or ensure mutability intentionally with `Collectors.toCollection(ArrayList::new)`.
- Prefer `Set` when uniqueness required; document ordering requirements.
- Use descriptive comparator: `.sorted(Comparator.comparing(Entity::getId).reversed())`.
- Favour unmodifiable collections when exposing read-only views
- Extract complex stream chains into named methods.

### Null Handling
- Use `Optional` judiciously for presence semantics, not to avoid null handling entirely
- Use `Optional` at API boundaries, not for internal fields unless modeling absence.
- Extract potentially null-derived values once: `var modificationType = actionProgress.getModificationType();`
- Prefer `Objects.requireNonNull` for mandatory constructor params.

---

## Spring Boot Code Style Guidelines

1. Dependency Injection Style
    * Don't use Spring Field Injection in production code.
    * Use Constructor Injection without adding `@Autowired`.

2. Transactional Boundaries
    * Make a business logic layer (@Service classes) as a transactional boundary.
    * Annotate methods that perform DB read-only operations with @Transactional(readOnly=true).
    * Annotate methods that perform DB write operations with @Transactional.
    * Keep transactions as short as possible.

3. Don't use JPA entities in the "web" layer
    * Instead, create dedicated Request/Response objects as Java records.
    * Use Jakarta Validation annotations on Request object.

4. Create custom Spring Data JPA methods with meaningful method names using JPQL queries instead of using long derived query method names.

5. Create usecase specific Command objects and pass them to the "service" layer methods to perform create or update operations.

6. Application Configuration:
    * Create all the application-specific configuration properties with a common prefix in `application.properties` file.
    * Use Typed Configuration with `@ConfigurationProperties` with validations.

7. Implement Global Exception Handling:
    * `@ControllerAdvice`/`@RestControllerAdvice` with `@ExceptionHandler` methods.
    * Return consistent error payloads (e.g. a standard `ErrorResponse` DTO).

8. Logging:
    * Never use `System.out.println()` for production logging.
    * Use SLF4J logging.

9. Use WebJars for service static content.

10. Don't use Lombok.

---
### Database Schema Management
Use Flyway for database migrations:

- Migration scripts should be in `src/main/resources/db/migration`
- Naming convention: `V{version}__{description}.sql`
- Hibernate is configured with `ddl-auto=validate` to ensure schema matches entities
- Single coherent migration, always create a corresponding rollback/undo script.
- Keep each flyway migration script idempotent
- Group related schema modifications per ticket into one migration; provide a corresponding undo when feasible.
- Increment version sequentially; avoid gaps & collisions.
- Keep test data out of production migrations; set up via test fixtures.

### Query Practices
- Prevent Extra queries, consolidate queries
- Prefer Spring Data derived queries / JPQL before native.
- Profile query count for complex operations; consolidate.
- Use projections or DTO queries to limit data transfer.

### Test Best Practices
1. **Unit Tests**: Test individual components in isolation using mocks if required
2. **Integration Tests**: Test interactions between components using Testcontainers
3. **Use descriptive test names** that explain what the test is verifying
4. **Follow the Given-When-Then pattern** for a clear test structure
5. **Use AssertJ for assertions** for more readable assertions
6. **Prefer testing with real dependencies** in unit tests as much as possible instead of using mocks
7. **Use Testcontainers for integration tests** to test with real databases, message brokers, etc
8. **TestcontainersConfiguration.java**: Configures database, message broker, etc containers for tests
9. **BaseIT.java**: Base class for integration tests that sets up:
    - Spring Boot test context using a random port
    - MockMvcTester for HTTP requests
    - Import `TestcontainersConfiguration.java`
10. **Min 80% Code Coverage**: Aim for good code coverage, but be pragmatic. Don't write useless tests just for the sake of code coverage metrics.

---
## Cross Functional Requirements (XFRs)

### Configuration Management
- Externalize configuration (e.g. application.yml + environment variables + Spring Cloud Config if available)
- Use placeholders / dummy values in examples and tests.
- Remove hard-coded profiles from base YAML (avoid forcing local profile).
- Maintain BOM (Bill of Materials) for dependency version alignment & vulnerability fixes.

### Performance Guidelines
- Leverage JPA batch operations or bulk repository methods.
- Cache repeated derived values (`modificationType`) outside loops.

### Bulk & Batch Operations
- Accumulate affected entity IDs, perform single update where possible.
- Wrap batch modifications in one transactional boundary.
- Use repository custom bulk operations (`deleteAllByIdInBatch`)


Customised on top of this [Original Source, Authored By SivaPrasad Reddy](https://gist.github.com/sivaprasadreddy/9751db630b819b39e5e87f5ecfb53346)